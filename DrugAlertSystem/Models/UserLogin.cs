using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

[PrimaryKey("LoginProvider", "ProviderKey")]
[Index("UserId", Name = "IX_UserLogins_UserId")]
public partial class UserLogin
{
    [Key]
    [StringLength(128)]
    public string LoginProvider { get; set; }

    [Key]
    [StringLength(128)]
    public string ProviderKey { get; set; }

    public string ProviderDisplayName { get; set; }

    [Required]
    public string UserId { get; set; }

    [ForeignKey("UserId")]
    [InverseProperty("UserLogins")]
    public virtual User User { get; set; }
}
