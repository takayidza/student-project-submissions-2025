using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore;
using WaterQM.Models;

namespace WaterQM.Data;

public partial class AppDbContext : DbContext
{
    public AppDbContext()
    {
    }

    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    public virtual DbSet<Alert> Alerts { get; set; }

    public virtual DbSet<Location> Locations { get; set; }

    public virtual DbSet<Notification> Notifications { get; set; }

    public virtual DbSet<Role> Roles { get; set; }

    public virtual DbSet<RoleClaim> RoleClaims { get; set; }

    public virtual DbSet<Sensor> Sensors { get; set; }

    public virtual DbSet<SensorReading> SensorReadings { get; set; }

    public virtual DbSet<Threshold> Thresholds { get; set; }

    public virtual DbSet<User> Users { get; set; }

    public virtual DbSet<UserClaim> UserClaims { get; set; }

    public virtual DbSet<UserLogin> UserLogins { get; set; }

    public virtual DbSet<UserToken> UserTokens { get; set; }

    public virtual DbSet<WaterParameter> WaterParameters { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        => optionsBuilder.UseSqlServer("name=AppConn");

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Alert>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Alerts__3213E83FC99252CC");

            entity.Property(e => e.AlertTime).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Sensor).WithMany(p => p.Alerts).HasConstraintName("FK_Alerts_Sensors");

            entity.HasOne(d => d.User).WithMany(p => p.Alerts)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("FK_Alerts_Users");
        });

        modelBuilder.Entity<Location>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Location__3213E83FA29C2546");
        });

        modelBuilder.Entity<Notification>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Notifica__3213E83F09A4C5AF");

            entity.Property(e => e.NotificationTime).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Alert).WithMany(p => p.Notifications).HasConstraintName("FK_Notifications_Alerts");

            entity.HasOne(d => d.User).WithMany(p => p.Notifications)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("FK_Notifications_Users");
        });

        modelBuilder.Entity<Role>(entity =>
        {
            entity.HasIndex(e => e.NormalizedName, "RoleNameIndex")
                .IsUnique()
                .HasFilter("([NormalizedName] IS NOT NULL)");
        });

        modelBuilder.Entity<Sensor>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Sensors__3213E83FDDDB4FD9");

            entity.HasOne(d => d.Location).WithMany(p => p.Sensors).HasConstraintName("FK_Sensors_Locations");
        });

        modelBuilder.Entity<SensorReading>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__SensorRe__3213E83FBC1863CB");

            entity.Property(e => e.ReadingTime).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Parameter).WithMany(p => p.SensorReadings).HasConstraintName("FK_SensorReadings_WaterParameters");

            entity.HasOne(d => d.Sensor).WithMany(p => p.SensorReadings).HasConstraintName("FK_SensorReadings_Sensors");
        });

        modelBuilder.Entity<Threshold>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Threshol__3213E83F5CCD23A6");

            entity.HasOne(d => d.Parameter).WithMany(p => p.Thresholds).HasConstraintName("FK_Thresholds_WaterParameters");
        });

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasMany(d => d.Roles).WithMany(p => p.Users)
                .UsingEntity<Dictionary<string, object>>(
                    "UserRole",
                    r => r.HasOne<Role>().WithMany().HasForeignKey("RoleId"),
                    l => l.HasOne<User>().WithMany()
                        .HasForeignKey("UserId")
                        .HasConstraintName("FK_UserRoles_AspNetUsers_UserId"),
                    j =>
                    {
                        j.HasKey("UserId", "RoleId");
                        j.ToTable("UserRoles");
                        j.HasIndex(new[] { "RoleId" }, "IX_UserRoles_RoleId");
                    });
        });

        modelBuilder.Entity<UserClaim>(entity =>
        {
            entity.HasOne(d => d.User).WithMany(p => p.UserClaims).HasConstraintName("FK_UserClaims_AspNetUsers_UserId");
        });

        modelBuilder.Entity<UserLogin>(entity =>
        {
            entity.HasOne(d => d.User).WithMany(p => p.UserLogins).HasConstraintName("FK_UserLogins_AspNetUsers_UserId");
        });

        modelBuilder.Entity<UserToken>(entity =>
        {
            entity.HasOne(d => d.User).WithMany(p => p.UserTokens).HasConstraintName("FK_UserTokens_AspNetUsers_UserId");
        });

        modelBuilder.Entity<WaterParameter>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__WaterPar__3213E83F7DFF38F1");
        });

        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
