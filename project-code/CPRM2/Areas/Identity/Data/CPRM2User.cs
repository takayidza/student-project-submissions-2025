using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Identity;

namespace CPRM2.Areas.Identity.Data;

// Add profile data for application users by adding properties to the CPRM2User class
public class CPRM2User : IdentityUser
{
    public string NationalId { get; set; }
    public string IdPhotoUrl { get; set; }
    public string LivePhotoUrl { get; set; }
    public bool IsVerified { get; set; } = false;
    public DateTime? VerificationDate { get; set; }
}


