using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace WaterQM.Models;

public partial class Notification
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("alert_id")]
    public int AlertId { get; set; }

    [Column("user_id")]
    [StringLength(450)]
    public string UserId { get; set; } = null!;

    [Column("notification_time", TypeName = "datetime")]
    public DateTime NotificationTime { get; set; }

    [ForeignKey("AlertId")]
    [InverseProperty("Notifications")]
    public virtual Alert Alert { get; set; } = null!;

    [ForeignKey("UserId")]
    [InverseProperty("Notifications")]
    public virtual User User { get; set; } = null!;
}
