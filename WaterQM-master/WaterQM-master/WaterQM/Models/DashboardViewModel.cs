namespace WaterQM.Models
{
    public class DashboardViewModel
    {
        public int TotalSensors { get; set; }
        public double AverageReading { get; set; }
        public List<SensorReading> LatestReadings { get; set; } = new();
        public List<SensorReading> Alerts { get; set; } = new();
    }
}
