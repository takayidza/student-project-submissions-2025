using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class Report
{
    [Key]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("user_id")]
    [StringLength(450)]
    public string UserId { get; set; }

    [Required]
    [Column("report_type")]
    [StringLength(50)]
    [Unicode(false)]
    public string ReportType { get; set; }

    [Column("description", TypeName = "text")]
    public string Description { get; set; }

    [Column("latitude")]
    public double Latitude { get; set; }

    [Column("longitude")]
    public double Longitude { get; set; }

    [Column("audio_data", TypeName = "varchar(255)")]
    [StringLength(255)]
    public string AudioData { get; set; }

    [Column("status")]
    [StringLength(20)]
    [Unicode(false)]
    public string Status { get; set; }

    [Column("created_at", TypeName = "datetime")]
    public DateTime? CreatedAt { get; set; }

    [InverseProperty("Report")]
    public virtual ICollection<Alert> Alerts { get; set; } = new List<Alert>();

    [InverseProperty("Report")]
    public virtual ICollection<DrugHotspotDatum> DrugHotspotData { get; set; } = new List<DrugHotspotDatum>();

    [InverseProperty("Report")]
    public virtual ICollection<LawEnforcementAction> LawEnforcementActions { get; set; } = new List<LawEnforcementAction>();

    [InverseProperty("Report")]
    public virtual ICollection<ReportStatusTracking> ReportStatusTrackings { get; set; } = new List<ReportStatusTracking>();

    [InverseProperty("Report")]
    public virtual ICollection<TrackingDatum> TrackingData { get; set; } = new List<TrackingDatum>();

    [ForeignKey("UserId")]
    [InverseProperty("Reports")]
    public virtual User User { get; set; }
}
