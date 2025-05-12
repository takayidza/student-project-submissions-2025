using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class LawEnforcementAction
{
    [Key]
    [Column("id")]
    public Guid Id { get; set; }

    [Column("report_id")]
    public Guid ReportId { get; set; }

    [Required]
    [Column("officer_id")]
    [StringLength(450)]
    public string OfficerId { get; set; }

    [Required]
    [Column("action_taken", TypeName = "text")]
    public string ActionTaken { get; set; }

    [Column("action_date", TypeName = "datetime")]
    public DateTime? ActionDate { get; set; }

    [ForeignKey("OfficerId")]
    [InverseProperty("LawEnforcementActions")]
    public virtual User Officer { get; set; }

    [ForeignKey("ReportId")]
    [InverseProperty("LawEnforcementActions")]
    public virtual Report Report { get; set; }
}
