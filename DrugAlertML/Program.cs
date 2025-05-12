using Microsoft.ML;
using Microsoft.ML.Data;
using Microsoft.ML.Trainers.FastTree;
using System;
using System.IO;
using System.Linq;

namespace DrugAlertML
{
    public class DrugHotspotData
    {
        [LoadColumn(0)]
        public string Location { get; set; }

        [LoadColumn(1)]
        public bool PeopleLoitering { get; set; }

        [LoadColumn(2)]
        public bool DrugWrappersFound { get; set; }

        [LoadColumn(3)]
        public bool StrongSmell { get; set; }

        [LoadColumn(4)]
        public bool LoudNoiseOrMusic { get; set; }

        [LoadColumn(5)]
        public bool ShoeHangingOnWire { get; set; }

        [LoadColumn(6)]
        public bool PeopleInAndOut { get; set; }

        [LoadColumn(7)]
        public bool IsHotspot { get; set; }
    }

    public class DrugHotspotPrediction
    {
        [ColumnName("PredictedLabel")]
        public bool IsHotspot { get; set; }

        [ColumnName("Probability")]
        public float Probability { get; set; }

        [ColumnName("Score")]
        public float Score { get; set; }
    }

    class Program
    {
        static void Main(string[] args)
        {
            var mlContext = new MLContext(seed: 42); // Set seed for reproducibility

            // Load the data
            var dataPath = Path.Combine(Environment.CurrentDirectory, "..", "DrugAlertSystem", "wwwroot", "drug_alert_complete_dataset (1).csv");
            var dataView = mlContext.Data.LoadFromTextFile<DrugHotspotData>(
                dataPath,
                hasHeader: true,
                separatorChar: ',');

            // Create the pipeline
            var pipeline = mlContext.Transforms.Categorical.OneHotEncoding("LocationEncoded", "Location")
                .Append(mlContext.Transforms.Conversion.ConvertType("PeopleLoiteringFloat", "PeopleLoitering", DataKind.Single))
                .Append(mlContext.Transforms.Conversion.ConvertType("DrugWrappersFoundFloat", "DrugWrappersFound", DataKind.Single))
                .Append(mlContext.Transforms.Conversion.ConvertType("StrongSmellFloat", "StrongSmell", DataKind.Single))
                .Append(mlContext.Transforms.Conversion.ConvertType("LoudNoiseOrMusicFloat", "LoudNoiseOrMusic", DataKind.Single))
                .Append(mlContext.Transforms.Conversion.ConvertType("ShoeHangingOnWireFloat", "ShoeHangingOnWire", DataKind.Single))
                .Append(mlContext.Transforms.Conversion.ConvertType("PeopleInAndOutFloat", "PeopleInAndOut", DataKind.Single))
                .Append(mlContext.Transforms.Concatenate("FeaturesRaw",
                    "LocationEncoded",
                    "PeopleLoiteringFloat",
                    "DrugWrappersFoundFloat",
                    "StrongSmellFloat",
                    "LoudNoiseOrMusicFloat",
                    "ShoeHangingOnWireFloat",
                    "PeopleInAndOutFloat"))
                .Append(mlContext.Transforms.NormalizeMinMax("Features", "FeaturesRaw")) // Normalize features
                .Append(mlContext.BinaryClassification.Trainers.FastTree(
                    new FastTreeBinaryTrainer.Options
                    {
                        NumberOfLeaves = 20,
                        MinimumExampleCountPerLeaf = 10,
                        LearningRate = 0.1,
                        NumberOfTrees = 100,
                        MaximumBinCountPerFeature = 254,
                        LabelColumnName = "IsHotspot",
                        FeatureColumnName = "Features"
                    }));

            // Perform cross-validation
            Console.WriteLine("Performing cross-validation...");
            var cvResults = mlContext.BinaryClassification.CrossValidate(
                data: dataView,
                estimator: pipeline,
                numberOfFolds: 5,
                labelColumnName: "IsHotspot"
            );

            // Print cross-validation metrics
            Console.WriteLine("\nCross-validation metrics:");
            Console.WriteLine($"Average Accuracy: {cvResults.Average(r => r.Metrics.Accuracy):P2}");
            Console.WriteLine($"Average AUC: {cvResults.Average(r => r.Metrics.AreaUnderRocCurve):P2}");
            Console.WriteLine($"Average F1 Score: {cvResults.Average(r => r.Metrics.F1Score):P2}");
            Console.WriteLine($"Standard Deviation of Accuracy: {StandardDeviation(cvResults.Select(r => r.Metrics.Accuracy)):P2}");

            // Train final model on full dataset
            Console.WriteLine("\nTraining final model on full dataset...");
            var model = pipeline.Fit(dataView);

            // Save the model
            mlContext.Model.Save(model, dataView.Schema, "DrugHotspotModel.zip");
            Console.WriteLine("Model saved as DrugHotspotModel.zip");

            // Create prediction engine
            var predictionEngine = mlContext.Model.CreatePredictionEngine<DrugHotspotData, DrugHotspotPrediction>(model);

            // Example predictions
            Console.WriteLine("\nSample Predictions:");

            // High risk example
            var highRiskSample = new DrugHotspotData
            {
                Location = "Mbare",
                PeopleLoitering = true,
                DrugWrappersFound = true,
                StrongSmell = true,
                LoudNoiseOrMusic = true,
                ShoeHangingOnWire = true,
                PeopleInAndOut = true
            };

            // Low risk example
            var lowRiskSample = new DrugHotspotData
            {
                Location = "Borrowdale",
                PeopleLoitering = false,
                DrugWrappersFound = false,
                StrongSmell = false,
                LoudNoiseOrMusic = false,
                ShoeHangingOnWire = false,
                PeopleInAndOut = false
            };

            // Medium risk example
            var mediumRiskSample = new DrugHotspotData
            {
                Location = "Gweru",
                PeopleLoitering = true,
                DrugWrappersFound = false,
                StrongSmell = true,
                LoudNoiseOrMusic = false,
                ShoeHangingOnWire = true,
                PeopleInAndOut = false
            };

            PredictAndPrint("High Risk Location", highRiskSample, predictionEngine);
            PredictAndPrint("Low Risk Location", lowRiskSample, predictionEngine);
            PredictAndPrint("Medium Risk Location", mediumRiskSample, predictionEngine);
        }

        private static void PredictAndPrint(string label, DrugHotspotData sample, PredictionEngine<DrugHotspotData, DrugHotspotPrediction> predictionEngine)
        {
            var prediction = predictionEngine.Predict(sample);
            Console.WriteLine($"\n{label}:");
            Console.WriteLine($"Location: {sample.Location}");
            Console.WriteLine($"Is Hotspot: {prediction.IsHotspot}");
            Console.WriteLine($"Probability: {prediction.Probability:P2}");
            Console.WriteLine($"Risk Score: {prediction.Score:F2}");
        }

        private static double StandardDeviation(IEnumerable<double> values)
        {
            var avg = values.Average();
            return Math.Sqrt(values.Average(v => Math.Pow(v - avg, 2)));
        }
    }
}
