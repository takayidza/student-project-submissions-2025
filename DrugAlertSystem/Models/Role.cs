using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Models;

public partial class Role
{
    [Key]
    public string Id { get; set; }

    [StringLength(256)]
    public string Name { get; set; }

    [StringLength(256)]
    public string NormalizedName { get; set; }

    public string ConcurrencyStamp { get; set; }

    [InverseProperty("Role")]
    public virtual ICollection<RoleClaim> RoleClaims { get; set; } = new List<RoleClaim>();

    [ForeignKey("RoleId")]
    [InverseProperty("Roles")]
    public virtual ICollection<User> Users { get; set; } = new List<User>();
}
