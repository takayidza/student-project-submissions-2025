using System.ComponentModel.DataAnnotations;

namespace DrugAlertSystem.Models
{
    public class DrugHotspotPredictionViewModel
    {
        [Required(ErrorMessage = "Location is required")]
        [Display(Name = "Location")]
        public string Location { get; set; } = string.Empty;

        [Display(Name = "People Loitering")]
        public bool PeopleLoitering { get; set; }

        [Display(Name = "Drug Wrappers Found")]
        public bool DrugWrappersFound { get; set; }

        [Display(Name = "Strong Smell")]
        public bool StrongSmell { get; set; }

        [Display(Name = "Loud Noise or Music")]
        public bool LoudNoiseOrMusic { get; set; }

        [Display(Name = "Shoe Hanging on Wire")]
        public bool ShoeHangingOnWire { get; set; }

        [Display(Name = "People In and Out")]
        public bool PeopleInAndOut { get; set; }

        public Guid ReportId { get; set; } 
    }

    public class DrugHotspotPredictionResultViewModel
    {
        public DrugHotspotPredictionViewModel Input { get; set; } = new();
        public bool IsHotspot { get; set; }
        public double Probability { get; set; }
        public double Score { get; set; }
    }
} 