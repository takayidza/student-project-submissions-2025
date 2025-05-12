using Microsoft.AspNetCore.Mvc;
using DrugAlertSystem.Services;

namespace DrugAlertSystem.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class DrugHotspotPredictionController : ControllerBase
    {
        private readonly DrugHotspotPredictionService _predictionService;

        public DrugHotspotPredictionController(DrugHotspotPredictionService predictionService)
        {
            _predictionService = predictionService;
        }

        [HttpPost("predict")]
        public IActionResult Predict([FromBody] DrugHotspotData data)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var prediction = _predictionService.Predict(data);
            return Ok(new
            {
                IsHotspot = prediction.IsHotspot,
                Probability = prediction.Probability,
                Score = prediction.Score
            });
        }
    }
}