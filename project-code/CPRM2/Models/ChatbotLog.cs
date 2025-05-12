using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace CPRM2.Models;

[Table("chatbot_logs")]
public partial class ChatbotLog
{
    [Key]
    [Column("chat_id")]
    public int ChatId { get; set; }

    [Column("user_id")]
    [StringLength(450)]
    public string UserId { get; set; }

    [Column("question", TypeName = "text")]
    public string Question { get; set; }

    [Column("answer", TypeName = "text")]
    public string Answer { get; set; }

    [Column("timestamp", TypeName = "datetime")]
    public DateTime? Timestamp { get; set; }

    [ForeignKey("UserId")]
    [InverseProperty("ChatbotLogs")]
    public virtual User User { get; set; }
}
