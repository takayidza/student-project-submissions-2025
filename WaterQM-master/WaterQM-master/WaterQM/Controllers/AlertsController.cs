using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using MimeKit;
using WaterQM.Areas.Identity.Data;
using WaterQM.Data;
using WaterQM.Models;

namespace WaterQM.Controllers
{
    [Authorize]
    public class AlertsController : Controller
    {
        private readonly AppDbContext _context;
        private readonly IConfiguration _configuration;
        private readonly UserManager<AppUser> _userManager;
        public AlertsController(AppDbContext context, IConfiguration configuration, UserManager<AppUser> userManager)
        {
            _context = context;
            _configuration = configuration;
            _userManager = userManager;
        }

        // GET: Alerts
        public async Task<IActionResult> Index()
        {
            var appDbContext = _context.Alerts.Include(a => a.Sensor).Include(a => a.User);

            var data = await appDbContext.ToListAsync();


            data = data.OrderByDescending(d => d.AlertTime).Take(200).ToList();
            return View(data);
        }

        // GET: Alerts/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var alert = await _context.Alerts
                .Include(a => a.Sensor)
                .Include(a => a.User)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (alert == null)
            {
                return NotFound();
            }

            return View(alert);
        }

        // GET: Alerts/Create
        public async Task<IActionResult> CreateTu()
        {
            var user = await _userManager.GetUserAsync(User);
            _context.Add(new Alert()
            {
                AlertMessage = "Low turbidity",
                AlertTime = DateTime.Now,
                SensorId = 2,
                UserId = user.Id,

            });

            await _context.SaveChangesAsync();

            return Ok();

        }
        public async Task<IActionResult> Create()
        {
            var user = await _userManager.GetUserAsync(User);
            _context.Add(new Alert()
            {
                AlertMessage = "alert on water levels",
                AlertTime = DateTime.Now,
                SensorId = 1,
                UserId = user.Id,

            });

            await _context.SaveChangesAsync();

            return Ok();
          
            // use mailkit/mimekit to send email without SSL certificate validation
            var emailConfig = _configuration.GetSection("EmailConfiguration");
            var smtpServer = emailConfig["SmtpServer"];
            var port = int.Parse(emailConfig["Port"]);
            var smtpUser = emailConfig["UserName"];
            var smtpPass = emailConfig["Password"];
            var fromAddress = emailConfig["From"];

            var email = new MimeMessage();
            email.From.Add(new MailboxAddress("water", fromAddress));
            email.To.Add(new MailboxAddress("", "maxmanetsa@gmail.com"));
            email.Subject = "Welcome to CPRM2 – Your Partner Portal Access";

            email.Body = new TextPart("plain")
            {
                Text = $@"alert on water evels"
            };


            using var smtpClient = new MailKit.Net.Smtp.SmtpClient();
            // disable SSL certificate validation
            smtpClient.ServerCertificateValidationCallback = (sender, certificate, chain, sslPolicyErrors) => true;
            await smtpClient.ConnectAsync(smtpServer, port, true);
            await smtpClient.AuthenticateAsync(smtpUser, smtpPass);
            await smtpClient.SendAsync(email);
            await smtpClient.DisconnectAsync(true);

            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id");
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id");
            return View();
        }

        // POST: Alerts/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("Id,SensorId,UserId,AlertMessage,AlertTime")] Alert alert)
        {
            if (ModelState.IsValid)
            {
                _context.Add(alert);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", alert.SensorId);
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", alert.UserId);
            return View(alert);
        }

        // GET: Alerts/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var alert = await _context.Alerts.FindAsync(id);
            if (alert == null)
            {
                return NotFound();
            }
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", alert.SensorId);
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", alert.UserId);
            return View(alert);
        }

        // POST: Alerts/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("Id,SensorId,UserId,AlertMessage,AlertTime")] Alert alert)
        {
            if (id != alert.Id)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(alert);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!AlertExists(alert.Id))
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
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", alert.SensorId);
            ViewData["UserId"] = new SelectList(_context.Users, "Id", "Id", alert.UserId);
            return View(alert);
        }

        // GET: Alerts/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var alert = await _context.Alerts
                .Include(a => a.Sensor)
                .Include(a => a.User)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (alert == null)
            {
                return NotFound();
            }

            return View(alert);
        }

        // POST: Alerts/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var alert = await _context.Alerts.FindAsync(id);
            if (alert != null)
            {
                _context.Alerts.Remove(alert);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool AlertExists(int id)
        {
            return _context.Alerts.Any(e => e.Id == id);
        }
    }
}
