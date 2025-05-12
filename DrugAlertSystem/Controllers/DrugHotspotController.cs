using Microsoft.AspNetCore.Mvc;
using DrugAlertSystem.Models;
using DrugAlertSystem.Services;
using DrugAlertSystem.Data;
using System.Threading.Tasks;

namespace DrugAlertSystem.Controllers
{
    public class DrugHotspotController : Controller
    {
        private readonly DrugHotspotPredictionService _predictionService;
        private readonly DrugsDbContext _context;

        public DrugHotspotController(DrugHotspotPredictionService predictionService, DrugsDbContext context)
        {
            _predictionService = predictionService;
            _context = context;
        }

        public IActionResult Predict(Guid id)
        {
            return View(new DrugHotspotPredictionViewModel() { ReportId = id});
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Predict(DrugHotspotPredictionViewModel model)
        {
            if (!ModelState.IsValid)
            {
                return View(model);
            }

            var data = new DrugHotspotData
            {
                Location = model.Location,
                PeopleLoitering = model.PeopleLoitering,
                DrugWrappersFound = model.DrugWrappersFound,
                StrongSmell = model.StrongSmell,
                LoudNoiseOrMusic = model.LoudNoiseOrMusic,
                ShoeHangingOnWire = model.ShoeHangingOnWire,
                PeopleInAndOut = model.PeopleInAndOut
            };

          

            var (isHotspot, probability, score) = _predictionService.GetPredictionResult(data);

            var result = new DrugHotspotPredictionResultViewModel
            {
                Input = model,
                IsHotspot = isHotspot,
                Probability = probability,
                Score = score
            };

            var dataToSave = new DrugHotspotDatum
            {
                ReportId = model.ReportId,
                Location = model.Location,
                PeopleLoitering = model.PeopleLoitering,
                DrugWrappersFound = model.DrugWrappersFound,
                StrongSmell = model.StrongSmell,
                LoudNoiseOrMusic = model.LoudNoiseOrMusic,
                ShoeHangingOnWire = model.ShoeHangingOnWire,
                PeopleInAndOut = model.PeopleInAndOut,
                Ishotspot = isHotspot,
                Probability = probability,
                Score = score
            };

            _context.DrugHotspotData.Add(dataToSave);
            await _context.SaveChangesAsync();

            return View("Result", result);
        }

        public IActionResult Result(DrugHotspotPredictionResultViewModel model)
        {
            return View(model);
        }
    }
}