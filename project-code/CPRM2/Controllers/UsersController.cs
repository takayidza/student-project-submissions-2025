using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Identity;
using CPRM2.Data;
using CPRM2.Models;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using CPRM2.Areas.Identity.Data;
using System.Text.Json.Serialization;
using System.Text;
using MimeKit;

namespace CPRM2.Controllers
{
    public class UsersController : Controller
    {
        private readonly CprmDbContext _context;
        private readonly UserManager<CPRM2User> _userManager;
        private readonly IWebHostEnvironment _webHostEnvironment;
        private readonly IConfiguration _configuration;

        public UsersController(
            CprmDbContext context,
            UserManager<CPRM2User> userManager,
            IWebHostEnvironment webHostEnvironment,
            IConfiguration configuration)
        {
            _context = context;
            _userManager = userManager;
            _webHostEnvironment = webHostEnvironment;
            _configuration = configuration;
        }

        // GET: Users
        public async Task<IActionResult> Index()
        {
            return View(await _context.Users.ToListAsync());
        }

        // GET: Users/Details/5
        public async Task<IActionResult> Details(string id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var user = await _context.Users
                .FirstOrDefaultAsync(m => m.Id == id);
            if (user == null)
            {
                return NotFound();
            }

            return View(user);
        }

        // GET: Users/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Users/Create
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([FromForm] User user, IFormFile idPhoto, string livePhoto)
        {
            if (!ModelState.IsValid)
            {
                return Json(new { success = false, message = "Invalid form data" });
            }

            try
            {
                // Save ID photo
                string idPhotoPath = await SavePhoto(idPhoto, "id_photos");
                user.IdPhotoUrl = idPhotoPath;

                // Save live photo
                string livePhotoPath = await SaveBase64Photo(livePhoto, "live_photos");
                user.LivePhotoUrl = livePhotoPath;

                // Verify faces using Face++
                bool isVerified = await VerifyFaces(idPhotoPath, livePhotoPath);

                if (!isVerified)
                {
                    // Delete the uploaded photos since verification failed
                    DeletePhoto(idPhotoPath);
                    DeletePhoto(livePhotoPath);

                    return Json(new
                    {
                        success = false,
                        message = "Face verification failed. Please ensure the live photo matches your ID photo."
                    });
                }

                user.IsVerified = true;
                user.VerificationDate = DateTime.UtcNow;

                var cprm2user = new CPRM2User
                {
                    Id = Guid.NewGuid().ToString(),
                    NationalId = user.NationalId,
                    IdPhotoUrl = user.IdPhotoUrl,
                    LivePhotoUrl = user.LivePhotoUrl,
                    IsVerified = true,
                    VerificationDate = DateTime.UtcNow,
                    UserName = user.UserName,
                    NormalizedUserName = user.UserName.ToUpper(),
                    Email = user.Email,
                    NormalizedEmail = user.Email.ToUpper(),
                    EmailConfirmed = true,
                    SecurityStamp = Guid.NewGuid().ToString(),
                    ConcurrencyStamp = Guid.NewGuid().ToString(),
                    PhoneNumber = user.PhoneNumber,
                    PhoneNumberConfirmed = user.PhoneNumberConfirmed,
                    TwoFactorEnabled = user.TwoFactorEnabled,
                    LockoutEnd = user.LockoutEnd,
                    LockoutEnabled = user.LockoutEnabled,
                    AccessFailedCount = user.AccessFailedCount
                };

                // Create user with UserManager
                var result = await _userManager.CreateAsync(cprm2user, "Pass-123");
                if (!result.Succeeded)
                {
                    // Delete the uploaded photos since user creation failed
                    DeletePhoto(idPhotoPath);
                    DeletePhoto(livePhotoPath);

                    return Json(new { success = false, message = string.Join(", ", result.Errors.Select(e => e.Description)) });
                }

                await _userManager.AddToRoleAsync(cprm2user, "Agent");

                // use mailkit/mimekit to send email without SSL certificate validation
                var emailConfig = _configuration.GetSection("EmailConfiguration");
                var smtpServer = emailConfig["SmtpServer"];
                var port = int.Parse(emailConfig["Port"]);
                var smtpUser = emailConfig["UserName"];
                var smtpPass = emailConfig["Password"];
                var fromAddress = emailConfig["From"];

                var email = new MimeMessage();
                email.From.Add(new MailboxAddress("CPRM2", fromAddress));
                email.To.Add(new MailboxAddress(user.UserName, user.Email));
                email.Subject = "Welcome to CPRM2 – Your Partner Portal Access";

                email.Body = new TextPart("plain")
                {
                    Text = $@"
                            Hello {user.UserName},

                            Welcome to CPRM2 – your Channel Partner Relationship Management portal.

                            You can now access tools to:
                            - View and order products like SIM cards, routers, and recharge vouchers
                            - Track commissions and transactions
                            - Upload and verify documents
                            - Chat with our support bot for help
                            - Access training materials to boost your sales

                            👉 To get started, log in on the website,   
                            (Use your email and the password you set during registration.)

                            Need help? Our support team is ready to assist via the chatbot or at support@yourcompany.com.

                            Thank you for partnering with us.

                            Best regards,  
                            The CPRM2 Team
                            "
                };


                using var smtpClient = new MailKit.Net.Smtp.SmtpClient();
                // disable SSL certificate validation
                smtpClient.ServerCertificateValidationCallback = (sender, certificate, chain, sslPolicyErrors) => true;
                await smtpClient.ConnectAsync(smtpServer, port, true);
                await smtpClient.AuthenticateAsync(smtpUser, smtpPass);
                await smtpClient.SendAsync(email);
                await smtpClient.DisconnectAsync(true);

                return Json(new { success = true });
            }
            catch (Exception ex)
            {
                // Try to clean up any uploaded photos in case of error
                try
                {
                    if (user.IdPhotoUrl != null) DeletePhoto(user.IdPhotoUrl);
                    if (user.LivePhotoUrl != null) DeletePhoto(user.LivePhotoUrl);
                }
                catch { /* Ignore cleanup errors */ }

                return Json(new { success = false, message = ex.Message });
            }
        }

        private async Task<string> SavePhoto(IFormFile photo, string folder)
        {
            if (photo == null || photo.Length == 0)
                throw new ArgumentException("No photo provided");

            string uploadsFolder = Path.Combine(_webHostEnvironment.WebRootPath, folder);
            if (!Directory.Exists(uploadsFolder))
                Directory.CreateDirectory(uploadsFolder);

            string uniqueFileName = $"{Guid.NewGuid()}_{photo.FileName}";
            string filePath = Path.Combine(uploadsFolder, uniqueFileName);

            using (var fileStream = new FileStream(filePath, FileMode.Create))
            {
                await photo.CopyToAsync(fileStream);
            }

            return $"/{folder}/{uniqueFileName}";
        }

        private async Task<string> SaveBase64Photo(string base64Photo, string folder)
        {
            if (string.IsNullOrEmpty(base64Photo))
                throw new ArgumentException("No photo provided");

            string uploadsFolder = Path.Combine(_webHostEnvironment.WebRootPath, folder);
            if (!Directory.Exists(uploadsFolder))
                Directory.CreateDirectory(uploadsFolder);

            string uniqueFileName = $"{Guid.NewGuid()}.jpg";
            string filePath = Path.Combine(uploadsFolder, uniqueFileName);

            // Remove data URL prefix if present
            if (base64Photo.Contains(","))
            {
                base64Photo = base64Photo.Split(',')[1];
            }

            byte[] photoBytes = Convert.FromBase64String(base64Photo);
            await System.IO.File.WriteAllBytesAsync(filePath, photoBytes);

            return $"/{folder}/{uniqueFileName}";
        }

        private async Task<bool> VerifyFaces(string idPhotoPath, string livePhotoPath)
        {
            try
            {
                var faceApiKey = _configuration.GetValue<string>("FacePlusPlus:ApiKey");
                var faceApiSecret = _configuration.GetValue<string>("FacePlusPlus:ApiSecret");

                if (string.IsNullOrEmpty(faceApiKey) || string.IsNullOrEmpty(faceApiSecret))
                {
                    Console.WriteLine("Face++ API credentials are missing in configuration");
                    return false;
                }

                // Get full physical paths for the images
                string idPhotoFullPath = Path.Combine(_webHostEnvironment.WebRootPath, idPhotoPath.TrimStart('/'));
                string livePhotoFullPath = Path.Combine(_webHostEnvironment.WebRootPath, livePhotoPath.TrimStart('/'));

                // Validate image files
                if (!ValidateImageFile(idPhotoFullPath) || !ValidateImageFile(livePhotoFullPath))
                {
                    Console.WriteLine("One or both images failed validation");
                    return false;
                }

                using (var client = new HttpClient())
                {
                    var compareUrl = "https://api-us.faceplusplus.com/facepp/v3/compare";
                    var formData = new MultipartFormDataContent();

                    Console.WriteLine($"API Key: [{faceApiKey}]");
                    Console.WriteLine($"API Secret: [{faceApiSecret}]");

                    // Add API credentials
                    formData.Add(new StringContent(faceApiKey, Encoding.UTF8), "api_key");
                    formData.Add(new StringContent(faceApiSecret, Encoding.UTF8), "api_secret");

                    var keyContent = new StringContent(faceApiKey, Encoding.UTF8);
                    keyContent.Headers.ContentDisposition = new System.Net.Http.Headers.ContentDispositionHeaderValue("form-data")
                    {
                        Name = "\"api_key\""
                    };

                    var secretContent = new StringContent(faceApiSecret, Encoding.UTF8);
                    secretContent.Headers.ContentDisposition = new System.Net.Http.Headers.ContentDispositionHeaderValue("form-data")
                    {
                        Name = "\"api_secret\""
                    };

                    formData.Add(keyContent);
                    formData.Add(secretContent);


                    // Add ID photo
                    var idPhotoBytes = await System.IO.File.ReadAllBytesAsync(idPhotoFullPath);
                    var idPhotoContent = new ByteArrayContent(idPhotoBytes);
                    idPhotoContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("image/jpeg");
                    formData.Add(idPhotoContent, "image_file1", "id_photo.jpg");

                    // Add live photo
                    var livePhotoBytes = await System.IO.File.ReadAllBytesAsync(livePhotoFullPath);
                    var livePhotoContent = new ByteArrayContent(livePhotoBytes);
                    livePhotoContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("image/jpeg");
                    formData.Add(livePhotoContent, "image_file2", "live_photo.jpg");

                    Console.WriteLine($"Sending request to Face++ API with image files: {idPhotoFullPath} and {livePhotoFullPath}");

                    var response = await client.PostAsync(compareUrl, formData);
                    var result = await response.Content.ReadAsStringAsync();

                    Console.WriteLine($"Face++ API Response Status: {response.StatusCode}");
                    Console.WriteLine($"Face++ API Response: {result}");

                    if (!response.IsSuccessStatusCode)
                    {
                        Console.WriteLine($"Face++ API Error: {result}");
                        return false;
                    }

                    var faceData = JsonSerializer.Deserialize<FaceCompareResponse>(result);

                    if (faceData?.Confidence == null)
                    {
                        Console.WriteLine("No confidence value returned from Face++ API");
                        return false;
                    }

                    Console.WriteLine($"Face++ Confidence: {faceData.Confidence}");

                    // Use the 1e-3 threshold as recommended by Face++ API
                    return faceData.Confidence > (faceData.Thresholds?.Threshold1e3 ?? 65.3);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in face verification: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                return false;
            }
        }

        private bool ValidateImageFile(string filePath)
        {
            try
            {
                // Check if file exists
                if (!System.IO.File.Exists(filePath))
                {
                    Console.WriteLine($"File does not exist: {filePath}");
                    return false;
                }

                // Check file size (max 2MB)
                var fileInfo = new FileInfo(filePath);
                if (fileInfo.Length > 2 * 1024 * 1024) // 2MB in bytes
                {
                    Console.WriteLine($"File too large: {filePath}");
                    return false;
                }

                // Check file extension
                var extension = Path.GetExtension(filePath).ToLower();
                if (extension != ".jpg" && extension != ".jpeg" && extension != ".png")
                {
                    Console.WriteLine($"Invalid file format: {filePath}");
                    return false;
                }

                // Check image dimensions
                using (var image = System.Drawing.Image.FromFile(filePath))
                {
                    if (image.Width < 48 || image.Width > 4096 || image.Height < 48 || image.Height > 4096)
                    {
                        Console.WriteLine($"Invalid image dimensions: {filePath}");
                        return false;
                    }
                }

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error validating image file {filePath}: {ex.Message}");
                return false;
            }
        }

        private void DeletePhoto(string photoPath)
        {
            if (string.IsNullOrEmpty(photoPath)) return;

            string fullPath = Path.Combine(_webHostEnvironment.WebRootPath, photoPath.TrimStart('/'));
            if (System.IO.File.Exists(fullPath))
            {
                System.IO.File.Delete(fullPath);
            }
        }

        // GET: Users/Edit/5
        public async Task<IActionResult> Edit(string id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var user = await _context.Users.FindAsync(id);
            if (user == null)
            {
                return NotFound();
            }
            return View(user);
        }

        // POST: Users/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(string id, [Bind("Id,NationalId,IdPhotoUrl,LivePhotoUrl,IsVerified,VerificationDate,UserName,NormalizedUserName,Email,NormalizedEmail,EmailConfirmed,PasswordHash,SecurityStamp,ConcurrencyStamp,PhoneNumber,PhoneNumberConfirmed,TwoFactorEnabled,LockoutEnd,LockoutEnabled,AccessFailedCount")] User user)
        {
            if (id != user.Id)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(user);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!UserExists(user.Id))
                    {
                        return NotFound();
                    }
                    else
                    {
                        throw;
                    }
                }
                return RedirectToAction(nameof(Index));
            }
            return View(user);
        }

        // GET: Users/Delete/5
        public async Task<IActionResult> Delete(string id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var user = await _context.Users
                .FirstOrDefaultAsync(m => m.Id == id);
            if (user == null)
            {
                return NotFound();
            }

            return View(user);
        }

        // POST: Users/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(string id)
        {
            var user = await _context.Users.FindAsync(id);
            if (user != null)
            {
                _context.Users.Remove(user);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool UserExists(string id)
        {
            return _context.Users.Any(e => e.Id == id);
        }
    }

    public class FaceCompareResponse
    {
        [JsonPropertyName("confidence")]
        public double? Confidence { get; set; }

        [JsonPropertyName("thresholds")]
        public Thresholds? Thresholds { get; set; }

        [JsonPropertyName("request_id")]
        public string? RequestId { get; set; }

        [JsonPropertyName("time_used")]
        public int TimeUsed { get; set; }

        [JsonPropertyName("error_message")]
        public string? ErrorMessage { get; set; }
    }

    public class Thresholds
    {
        [JsonPropertyName("1e-3")]
        public double Threshold1e3 { get; set; }

        [JsonPropertyName("1e-4")]
        public double Threshold1e4 { get; set; }

        [JsonPropertyName("1e-5")]
        public double Threshold1e5 { get; set; }
    }
}
