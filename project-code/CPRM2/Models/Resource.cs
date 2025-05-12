using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace CPRM2.Models;

[Table("resources")]
public partial class Resource
{
    [Key]
    [Column("resource_id")]
    public int ResourceId { get; set; }

    [Column("title")]
    [StringLength(100)]
    [Unicode(false)]
    public string Title { get; set; }

    [Column("file_url")]
    [StringLength(255)]
    [Unicode(false)]
    public string FileUrl { get; set; }

    [Column("category")]
    [StringLength(50)]
    [Unicode(false)]
    public string Category { get; set; }

    [Column("uploaded_at", TypeName = "datetime")]
    public DateTime? UploadedAt { get; set; }
}
