import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reports.component.html',
  styleUrl: './reports.component.css'
})
export class ReportsComponent implements OnInit {
  private supabase: SupabaseClient;
  totalPatients: number = 0;
  totalAppointments: number = 0;
  totalPrescriptions: number = 0;
  bookedDates: Date[] = [];
  currentMonth: Date = new Date();

  constructor() {
    this.supabase = createClient('https://eximxyncuxlgoqwvczmh.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc');
  }

  async ngOnInit() {
    await this.fetchCounts();
    await this.fetchBookedDates();
  }

  async fetchCounts() {
    // Patients count
    const { count: patientCount } = await this.supabase
      .from('patient_profile')
      .select('*', { count: 'exact', head: true });
    this.totalPatients = patientCount ?? 0;

    // Appointments count
    const { count: appointmentCount } = await this.supabase
      .from('appointments')
      .select('*', { count: 'exact', head: true });
    this.totalAppointments = appointmentCount ?? 0;

    // Prescriptions count
    const { count: prescriptionCount } = await this.supabase
      .from('prescription')
      .select('*', { count: 'exact', head: true });
    this.totalPrescriptions = prescriptionCount ?? 0;
  }

  async fetchBookedDates() {
    const { data, error } = await this.supabase
      .from('appointments')
      .select('appointment_date'); // adjust 'appointment_date' to your actual date field
    if (error) {
      console.error('Error fetching booked dates:', error);
    }
    if (data) {
      console.log("dates ..............", data);
      this.bookedDates = data.map((item: any) => new Date(item.appointment_date));
    }
  }

  getCalendar(): (Date | null)[][] {
    const year = this.currentMonth.getFullYear();
    const month = this.currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    const weeks: (Date | null)[][] = [];
    let week: (Date | null)[] = new Array(firstDay.getDay()).fill(null);

    for (let d = 1; d <= lastDay.getDate(); d++) {
      week.push(new Date(year, month, d));
      if (week.length === 7) {
        weeks.push(week);
        week = [];
      }
    }
    if (week.length > 0) {
      while (week.length < 7) week.push(null);
      weeks.push(week);
    }
    return weeks;
  }

  
  isBookedDate(date: Date | null): boolean {
    // console.log(this.getCalendar());
    if (!date) return false;
    return this.bookedDates.some(
      d => d.getFullYear() === date.getFullYear() &&
           d.getMonth() === date.getMonth() &&
           d.getDate() === date.getDate()
    );
  }


}
