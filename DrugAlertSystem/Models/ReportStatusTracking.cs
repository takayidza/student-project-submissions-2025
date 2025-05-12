using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

[Table("ReportStatusTracking")]
public partial class ReportStatusTracking
{
    [Key]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("report_id")]
    public Guid ReportId { get; set; }

    [Required]
    [Column("previous_status")]
    [StringLength(20)]
    [Unicode(false)]
    public string PreviousStatus { get; set; }

    [Required]
    [Column("new_status")]
    [StringLength(20)]
    [Unicode(false)]
    public string NewStatus { get; set; }

    [Required]
    [Column("updated_by")]
    [StringLength(450)]
    public string UpdatedBy { get; set; }

    [Column("updated_at", TypeName = "datetime")]
    public DateTime? UpdatedAt { get; set; }

    [ForeignKey("ReportId")]
    [InverseProperty("ReportStatusTrackings")]
    public virtual Report Report { get; set; }

    [ForeignKey("UpdatedBy")]
    [InverseProperty("ReportStatusTrackings")]
    public virtual User UpdatedByNavigation { get; set; }
}
