using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using WaterQM.Data;
using WaterQM.Models;

public class HomeController : Controller
{
    private readonly AppDbContext _context;
    private readonly Random _random = new Random();

    public HomeController(AppDbContext context)
    {
        _context = context;
    }

    public IActionResult Index()
    {
        // Fetch all sensor readings
        var sensorReadings = _context.SensorReadings
            .Include(s => s.Sensor)
            .Include(s => s.Parameter)
            .ToList();

        // Update readings with random values
        foreach (var reading in sensorReadings)
        {
            reading.ReadingValue = GetRandomReading(reading.ParameterId);
            reading.ReadingTime = DateTime.Now;
        }
        _context.SaveChanges();

        // Dashboard Summary Data
        var totalSensors = _context.Sensors.Count();
        var latestReadings = sensorReadings.OrderByDescending(s => s.ReadingTime).Take(10).ToList();
        var avgReading = sensorReadings.Any() ? sensorReadings.Average(s => s.ReadingValue) : 0;
        var alertReadings = sensorReadings.Where(s => s.ReadingValue > 15).Take(5).ToList();

        var model = new DashboardViewModel
        {
            TotalSensors = totalSensors,
            AverageReading = Math.Round(avgReading, 2),
            LatestReadings = latestReadings,
            Alerts = alertReadings
        };

        return View(model);
    }

    private double GetRandomReading(int parameterId)
    {
        return parameterId switch
        {
            1 => Math.Round(_random.NextDouble() * (9 - 6) + 6, 2), // pH range 6-9
            2 => Math.Round(_random.NextDouble() * 20, 1), // Turbidity 0-20 NTU
            3 => Math.Round(_random.NextDouble() * 10, 1), // Dissolved Oxygen 0-10 mg/L
            _ => Math.Round(_random.NextDouble() * 100, 1) // Generic values
        };
    }

 

}
