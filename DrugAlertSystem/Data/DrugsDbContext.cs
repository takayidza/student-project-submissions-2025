using System;
using System.Collections.Generic;
using DrugAlertSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace DrugAlertSystem.Data;

public partial class DrugsDbContext : DbContext
{
    public DrugsDbContext()
    {
    }

    public DrugsDbContext(DbContextOptions<DrugsDbContext> options)
        : base(options)
    {
    }

    public virtual DbSet<Alert> Alerts { get; set; }

    public virtual DbSet<DrugHotspotDatum> DrugHotspotData { get; set; }

    public virtual DbSet<LawEnforcementAction> LawEnforcementActions { get; set; }

    public virtual DbSet<Report> Reports { get; set; }

    public virtual DbSet<ReportStatusTracking> ReportStatusTrackings { get; set; }

    public virtual DbSet<Role> Roles { get; set; }

    public virtual DbSet<RoleClaim> RoleClaims { get; set; }

    public virtual DbSet<TrackingDatum> TrackingData { get; set; }

    public virtual DbSet<User> Users { get; set; }

    public virtual DbSet<UserClaim> UserClaims { get; set; }

    public virtual DbSet<UserLogin> UserLogins { get; set; }

    public virtual DbSet<UserToken> UserTokens { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        => optionsBuilder.UseSqlServer("name=DrugsConn");

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Alert>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Alerts__3213E83F2D99D882");

            entity.Property(e => e.Id).HasDefaultValueSql("(newid())");
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("(getdate())");
            entity.Property(e => e.IsFalseReport).HasDefaultValue(false);

            entity.HasOne(d => d.Report).WithMany(p => p.Alerts).HasConstraintName("FK__Alerts__report_i__6754599E");
        });

        modelBuilder.Entity<DrugHotspotDatum>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__DrugHots__3214EC079EC2CC88");

            entity.HasOne(d => d.Report).WithMany(p => p.DrugHotspotData).HasConstraintName("FK__DrugHotsp__Repor__1EA48E88");
        });

        modelBuilder.Entity<LawEnforcementAction>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__LawEnfor__3213E83FE09A123D");

            entity.Property(e => e.Id).HasDefaultValueSql("(newid())");
            entity.Property(e => e.ActionDate).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Officer).WithMany(p => p.LawEnforcementActions).HasConstraintName("FK__LawEnforc__offic__6D0D32F4");

            entity.HasOne(d => d.Report).WithMany(p => p.LawEnforcementActions).HasConstraintName("FK__LawEnforc__repor__6C190EBB");
        });

        modelBuilder.Entity<Report>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Reports__3213E83FA70185D7");

            entity.Property(e => e.Id).HasDefaultValueSql("(newid())");
            entity.Property(e => e.CreatedAt).HasDefaultValueSql("(getdate())");
            entity.Property(e => e.Status).HasDefaultValue("Pending");

            entity.HasOne(d => d.User).WithMany(p => p.Reports)
                .OnDelete(DeleteBehavior.SetNull)
                .HasConstraintName("FK__Reports__user_id__619B8048");
        });

        modelBuilder.Entity<ReportStatusTracking>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__ReportSt__3213E83F06438642");

            entity.Property(e => e.Id).HasDefaultValueSql("(newid())");
            entity.Property(e => e.UpdatedAt).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Report).WithMany(p => p.ReportStatusTrackings).HasConstraintName("FK__ReportSta__repor__71D1E811");

            entity.HasOne(d => d.UpdatedByNavigation).WithMany(p => p.ReportStatusTrackings).HasConstraintName("FK__ReportSta__updat__72C60C4A");
        });

        modelBuilder.Entity<Role>(entity =>
        {
            entity.HasIndex(e => e.NormalizedName, "RoleNameIndex")
                .IsUnique()
                .HasFilter("([NormalizedName] IS NOT NULL)");
        });

        modelBuilder.Entity<TrackingDatum>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PK__Tracking__3213E83F0A881C53");

            entity.Property(e => e.Id).HasDefaultValueSql("(newid())");
            entity.Property(e => e.FlaggedDate).HasDefaultValueSql("(getdate())");

            entity.HasOne(d => d.Report).WithMany(p => p.TrackingData)
                .OnDelete(DeleteBehavior.Cascade)
                .HasConstraintName("FK__TrackingD__repor__787EE5A0");
        });

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasIndex(e => e.NormalizedUserName, "UserNameIndex")
                .IsUnique()
                .HasFilter("([NormalizedUserName] IS NOT NULL)");

            entity.HasMany(d => d.Roles).WithMany(p => p.Users)
                .UsingEntity<Dictionary<string, object>>(
                    "UserRole",
                    r => r.HasOne<Role>().WithMany().HasForeignKey("RoleId"),
                    l => l.HasOne<User>().WithMany().HasForeignKey("UserId"),
                    j =>
                    {
                        j.HasKey("UserId", "RoleId");
                        j.ToTable("UserRoles");
                        j.HasIndex(new[] { "RoleId" }, "IX_UserRoles_RoleId");
                    });
        });

        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
