using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class Alert
{
    [Key]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("report_id")]
    public Guid ReportId { get; set; }

    [Required]
    [Column("alert_level")]
    [StringLength(20)]
    [Unicode(false)]
    public string AlertLevel { get; set; }

    [Column("is_false_report")]
    public bool? IsFalseReport { get; set; }

    [Column("created_at", TypeName = "datetime")]
    public DateTime? CreatedAt { get; set; }

    [ForeignKey("ReportId")]
    [InverseProperty("Alerts")]
    public virtual Report Report { get; set; }
}
