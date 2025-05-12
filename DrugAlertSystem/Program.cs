using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using DrugAlertSystem.Data;
using DrugAlertSystem.Areas.Identity.Data;
using DrugAlertSystem.Services;
var builder = WebApplication.CreateBuilder(args);
var connectionString = builder.Configuration.GetConnectionString("DrugsConn") ?? throw new InvalidOperationException("Connection string 'DrugsIdentityDbContextConnection' not found.");

builder.Services.AddDbContext<DrugsIdentityDbContext>(options => options.UseSqlServer(connectionString));

builder.Services.AddDbContext<DrugsDbContext>(options =>
    options.UseSqlServer(connectionString));

builder.Services.AddDefaultIdentity<DrugsUser>(options =>
    options.SignIn.RequireConfirmedAccount = false)
    .AddRoles<IdentityRole>() // ? This is required to enable roles
    .AddEntityFrameworkStores<DrugsIdentityDbContext>()
    .AddRoleManager<RoleManager<IdentityRole>>(); // ? Use RoleManager<IdentityRole>

builder.Services.AddScoped<DrugHotspotPredictionService>();

builder.Services.AddRazorPages();
// Add services to the container.
builder.Services.AddControllersWithViews();

builder.Services.AddMvc();

builder.Services.AddProgressiveWebApp();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseAuthorization();
app.MapRazorPages();
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
