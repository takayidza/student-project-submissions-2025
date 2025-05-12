using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class TrackingDatum
{
    [Key]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("report_id")]
    public Guid? ReportId { get; set; }

    [Column("latitude", TypeName = "decimal(9, 6)")]
    public decimal Latitude { get; set; }

    [Column("longitude", TypeName = "decimal(9, 6)")]
    public decimal Longitude { get; set; }

    [Required]
    [Column("tracking_type")]
    [StringLength(20)]
    [Unicode(false)]
    public string TrackingType { get; set; }

    [Column("map_pin_color")]
    [StringLength(10)]
    [Unicode(false)]
    public string MapPinColor { get; set; }

    [Column("flagged_date", TypeName = "datetime")]
    public DateTime? FlaggedDate { get; set; }

    [Column("reason", TypeName = "text")]
    public string Reason { get; set; }

    [ForeignKey("ReportId")]
    [InverseProperty("TrackingData")]
    public virtual Report Report { get; set; }
}
