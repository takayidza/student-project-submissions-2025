using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using DrugAlertSystem.Data;
using DrugAlertSystem.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using DrugAlertSystem.Areas.Identity.Data;
using Microsoft.AspNetCore.Mvc.ModelBinding.Validation;
using Microsoft.AspNetCore.Http;
using System.IO;

namespace DrugAlertSystem.Controllers
{
    [Authorize]
    public class ReportsController : Controller
    {
        private readonly DrugsDbContext _context;
        private readonly UserManager<DrugsUser> _userManager;

        public ReportsController(DrugsDbContext context, UserManager<DrugsUser> userManager)
        {
            _context = context;
            _userManager = userManager;
        }

        // GET: Reports
        public async Task<IActionResult> Index()
        {

            try
            {
             //   await _context.Database.ExecuteSqlRawAsync("alter table reports drop column  audio_data ");
             //   await _context.Database.ExecuteSqlRawAsync("alter table reports add  audio_data nvarchar(max)");
            }
            catch (System.Exception)
            {


            }

            var user = await _userManager.GetUserAsync(User);
            var userId = user?.Id;

            // Check if user is in an admin or law enforcement role
            bool isAdminOrLawEnforcement = User.IsInRole("Admin") || User.IsInRole("LawEnforcement");

            var reports = isAdminOrLawEnforcement
                ? _context.Reports.Include(r => r.User) // Return all reports for Admin/Law Enforcement
                : _context.Reports.Where(r => r.UserId == userId).Include(r => r.User); // Return only user's reports

            var data = await reports.OrderByDescending(d => d.CreatedAt).ToListAsync();

            foreach (var item in data)
            {
                if (item.User !=null)
                {
                    var count = data.Count(d => d.UserId == item.UserId);
                    var resolvedCount = data.Count(d => d.UserId == item.UserId && d.Status == "Resolved");

                    if (count > 0)
                    {
                        var percentage = (double)resolvedCount /(double) count * 100;

                        item.User.ConcurrencyStamp = percentage switch
                        {
                            < 20 => "*",    // 1 star
                            < 40 => "**",   // 2 stars
                            < 60 => "***",  // 3 stars
                            < 80 => "****", // 4 stars
                            _ => "*****"    // 5 stars
                        };
                    }
                    else
                    {
                        // Handle case where count is 0 (e.g., set ConcurrencyStamp to empty or a default value)
                        item.User.ConcurrencyStamp = "*"; // or some default value
                    }
                }
            }

            return View(data);
        }


        // GET: Reports/Details/5
        public async Task<IActionResult> Details(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var report = await _context.Reports
                .Include(d => d.DrugHotspotData)
                .Include(r => r.User)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (report == null)
            {
                return NotFound();
            }

            return View(report);
        }

        // GET: Reports/Create

        public async Task<IActionResult> Create()
        {

            var user = (await _userManager.GetUserAsync(User));


            ViewData["UserId"] = user.Id;
            return View(new Report() { UserId = user.Id });
        }

        // POST: Reports/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]

        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([ValidateNever] Report report)
        {
            var user = (await _userManager.GetUserAsync(User));

            report.UserId = user.Id;

            if (ModelState.IsValid)
            {
                report.Id = Guid.NewGuid();

                _context.Add(report);
                await _context.SaveChangesAsync();
                return RedirectToAction("Predict", "DrugHotspot", new { id = report.Id });
            }
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", report.UserId);
            return View(report);
        }

        // GET: Reports/Edit/5
        public async Task<IActionResult> Edit(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var report = await _context.Reports.FindAsync(id);
            if (report == null)
            {
                return NotFound();
            }
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", report.UserId);
            return View(report);
        }

        // POST: Reports/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(Guid id, Report report)
        {
            if (id != report.Id)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(report);
                    await _context.SaveChangesAsync();


                    if(report.Status == "Resolved")
                    {
                       await _context.Database.ExecuteSqlRawAsync($"update users set AccessFailedCount = AccessFailedCount+1 where id = '{report.UserId}'");
                    }

                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!ReportExists(report.Id))
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
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", report.UserId);
            return View(report);
        }

        // GET: Reports/Delete/5
        public async Task<IActionResult> Delete(Guid? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var report = await _context.Reports
                .Include(r => r.User)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (report == null)
            {
                return NotFound();
            }

            return View(report);
        }

        // POST: Reports/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(Guid id)
        {
            var report = await _context.Reports.FindAsync(id);
            if (report != null)
            {
                _context.Reports.Remove(report);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool ReportExists(Guid id)
        {
            return _context.Reports.Any(e => e.Id == id);
        }

        [HttpPost]
        public async Task<IActionResult> UploadAudio(IFormFile audioFile)
        {
            if (audioFile == null || audioFile.Length == 0)
            {
                return BadRequest("No file uploaded");
            }

            try
            {
                // Create uploads directory if it doesn't exist
                var uploadsDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads", "audio");
                if (!Directory.Exists(uploadsDir))
                {
                    Directory.CreateDirectory(uploadsDir);
                }

                // Generate unique filename
                var fileName = $"{Guid.NewGuid()}.wav";
                var filePath = Path.Combine(uploadsDir, fileName);

                // Save the file
                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    await audioFile.CopyToAsync(stream);
                }

                // Return the relative URL
                var fileUrl = $"/uploads/audio/{fileName}";
                return Json(new { fileUrl });
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }
    }
}
