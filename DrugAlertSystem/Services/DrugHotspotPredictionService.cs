using Microsoft.ML;
using System.IO;

namespace DrugAlertSystem.Services
{
    public class DrugHotspotPredictionService
    {
        private readonly PredictionEngine<DrugHotspotData, DrugHotspotPrediction> _predictionEngine;

        public DrugHotspotPredictionService()
        {
            var mlContext = new MLContext();
            var modelPath = Path.Combine(Directory.GetCurrentDirectory(), "DrugHotspotModel.zip");

            if (!File.Exists(modelPath))
            {
                throw new FileNotFoundException("ML model file not found. Please ensure DrugHotspotModel.zip exists in the application root directory.");
            }

            var model = mlContext.Model.Load(modelPath, out var modelSchema);
            _predictionEngine = mlContext.Model.CreatePredictionEngine<DrugHotspotData, DrugHotspotPrediction>(model);
        }

        public DrugHotspotPrediction Predict(DrugHotspotData data)
        {
            if (data == null)
            {
                throw new ArgumentNullException(nameof(data));
            }

            if (string.IsNullOrWhiteSpace(data.Location))
            {
                throw new ArgumentException("Location is required", nameof(data.Location));
            }

            return _predictionEngine.Predict(data);
        }

        public (bool IsHotspot, double Probability, double Score) GetPredictionResult(DrugHotspotData data)
        {
            var prediction = Predict(data);
            return (prediction.IsHotspot, prediction.Probability, prediction.Score);
        }
    }

    public class DrugHotspotData
    {
        public string Location { get; set; } = string.Empty;
        public bool PeopleLoitering { get; set; }
        public bool DrugWrappersFound { get; set; }
        public bool StrongSmell { get; set; }
        public bool LoudNoiseOrMusic { get; set; }
        public bool ShoeHangingOnWire { get; set; }
        public bool PeopleInAndOut { get; set; }
    }

    public class DrugHotspotPrediction
    {
        public bool IsHotspot { get; set; }
        public float Probability { get; set; }
        public float Score { get; set; }
    }
}