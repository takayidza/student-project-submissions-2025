using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Linq;
using System.Threading.Tasks;
using AspNetCoreGeneratedDocument;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Infrastructure;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using WaterQM.Areas.Identity.Data;
using WaterQM.Data;
using WaterQM.Models;

namespace WaterQM.Controllers
{
    [Authorize]
    public class SensorReadingsController : Controller
    {
        private readonly AppDbContext _context;
        private readonly IHubContext<SensorHub> _hubContext;
        private static SerialPort _serialPort;
        private bool found=true;
        private UserManager<AppUser> _userManager;
        private AppUser user;
        public SensorReadingsController(AppDbContext context, IHubContext<SensorHub> hubContext, UserManager<AppUser> userManager)
        {
          
            _hubContext = hubContext;
            _userManager = userManager;
            _context = context;


            // Open Serial Port if not already open
            if (_serialPort == null)
            {
                _serialPort = new SerialPort("COM4", 9600);
                _serialPort.DataReceived += SerialDataReceived;
                 
                    _serialPort.Open();
                
            }
            user = new AppUser();
            user.Id = "47671c8c-3d6f-448e-a2e8-4a155727686a";


        }

        private async void SerialDataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            try
            {
                string data = _serialPort.ReadLine();
                string[] values = data.Split(',');

                // Check if we have 3 values now (pH, water level, and turbidity)
                if (values.Length == 3 &&
                    float.TryParse(values[0], out float phValue) &&
                    float.TryParse(values[1], out float waterLevelValue) &&
                    float.TryParse(values[2], out float turbidityValue))
                {
                    // Create pH reading
                    var phReading = new SensorReading
                    {
                        ParameterId = 1, // pH parameter
                        ReadingTime = DateTime.Now,
                        ReadingValue = phValue,
                        SensorId = 1
                    };

                    // Create water level reading
                    var waterLevelReading = new SensorReading
                    {
                        ParameterId = 2, // Water level parameter
                        ReadingTime = DateTime.Now,
                        ReadingValue = waterLevelValue,
                        SensorId = 2
                    };

                    // Create turbidity reading
                    var turbidityReading = new SensorReading
                    {
                        ParameterId = 3, // Turbidity parameter
                        ReadingTime = DateTime.Now,
                        ReadingValue = turbidityValue,
                        SensorId = 3
                    };

                    // Check pH thresholds and create notification if necessary
                    if (phReading.ReadingValue > 8.5 || phReading.ReadingValue < 6.5)
                    {
                        Notification notification = new Notification()
                        {
                            NotificationTime = DateTime.Now,
                            Alert = new Alert()
                            {
                                AlertMessage = phReading.ReadingValue > 8.5 ? "pH level is too high" : "pH level is too low",
                                AlertTime = DateTime.Now,
                                UserId = user.Id,
                                SensorId = 1,
                            }
                        };
                  //      _context.Add(notification);
                    }

                    // Check water level thresholds and create notification if necessary
                    if (waterLevelReading.ReadingValue < 2)
                    {
                        Notification notification = new Notification()
                        {
                            NotificationTime = DateTime.Now,
                            Alert = new Alert()
                            {
                                AlertMessage = "Water level is too low",
                                AlertTime = DateTime.Now,
                                UserId = user.Id,
                                SensorId = 2,
                            }
                        };
                  //      _context.Add(notification);
                    }

                    // Check turbidity thresholds and create notification if necessary
                    // Adjust these thresholds based on your requirements
                    // Higher NTU value means more turbid water
                    if (turbidityReading.ReadingValue > 25)
                    {
                        Notification notification = new Notification()
                        {
                            NotificationTime = DateTime.Now,
                            Alert = new Alert()
                            {
                                AlertMessage = "Water turbidity is too high",
                                AlertTime = DateTime.Now,
                                UserId = user.Id,
                                SensorId = 3,
                            }
                        };
                     //   _context.Add(notification);
                    }

                    // Save all readings to Database
                  //  _context.Add(phReading);
                  //  _context.Add(waterLevelReading);
                  ///  _context.Add(turbidityReading);
                  //   _context.SaveChanges();

                    // Send data to frontend via SignalR - now including turbidity
                    await _hubContext.Clients.All.SendAsync("ReceiveSensorData",
                        phValue,
                        waterLevelValue,
                        turbidityValue,
                        phReading.ReadingTime.ToString("HH:mm:ss"));
                }
                else
                {
                    // Log that the data format was incorrect
                    Console.WriteLine($"Received invalid data format: {data}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
        }
        // GET: SensorReadings
        public async Task<IActionResult> Index()
        { 

            if (found == false)
            {
                ViewData["Message"] = "Sensor not found";
            }

            return View(new List<SensorReading>());
        }

        // GET: SensorReadings/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var sensorReading = await _context.SensorReadings
                .Include(s => s.Parameter)
                .Include(s => s.Sensor)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (sensorReading == null)
            {
                return NotFound();
            }

            return View(sensorReading);
        }

        // GET: SensorReadings/Create
        public IActionResult Create()
        {
            ViewData["ParameterId"] = new SelectList(_context.WaterParameters, "Id", "Id");
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id");
            return View();
        }
        
        //public async Task<IActionResult> PlotAndSave()
        //{

        //    //code to save
        //    var reading = new SensorReading()
        //    {
        //        ParameterId = 1,
        //        ReadingTime = DateTime.Now,
        //        ReadingValue =, //value from iot ,
        //        SensorId = 1,


        //    };

        //    _context.Add(reading);
        //    await _context.SaveChangesAsync();
        //    ////code to plot
        //    ///



        //    return View();
        //}

        // POST: SensorReadings/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("Id,SensorId,ParameterId,ReadingValue,ReadingTime")] SensorReading sensorReading)
        {
            if (ModelState.IsValid)
            {
                _context.Add(sensorReading);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            ViewData["ParameterId"] = new SelectList(_context.WaterParameters, "Id", "Id", sensorReading.ParameterId);
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", sensorReading.SensorId);
            return View(sensorReading);
        }

        // GET: SensorReadings/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var sensorReading = await _context.SensorReadings.FindAsync(id);
            if (sensorReading == null)
            {
                return NotFound();
            }
            ViewData["ParameterId"] = new SelectList(_context.WaterParameters, "Id", "Id", sensorReading.ParameterId);
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", sensorReading.SensorId);
            return View(sensorReading);
        }

        // POST: SensorReadings/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("Id,SensorId,ParameterId,ReadingValue,ReadingTime")] SensorReading sensorReading)
        {
            if (id != sensorReading.Id)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(sensorReading);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!SensorReadingExists(sensorReading.Id))
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
            ViewData["ParameterId"] = new SelectList(_context.WaterParameters, "Id", "Id", sensorReading.ParameterId);
            ViewData["SensorId"] = new SelectList(_context.Sensors, "Id", "Id", sensorReading.SensorId);
            return View(sensorReading);
        }

        // GET: SensorReadings/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var sensorReading = await _context.SensorReadings
                .Include(s => s.Parameter)
                .Include(s => s.Sensor)
                .FirstOrDefaultAsync(m => m.Id == id);
            if (sensorReading == null)
            {
                return NotFound();
            }

            return View(sensorReading);
        }

        // POST: SensorReadings/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var sensorReading = await _context.SensorReadings.FindAsync(id);
            if (sensorReading != null)
            {
                _context.SensorReadings.Remove(sensorReading);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool SensorReadingExists(int id)
        {
            return _context.SensorReadings.Any(e => e.Id == id);
        }
    }
}
