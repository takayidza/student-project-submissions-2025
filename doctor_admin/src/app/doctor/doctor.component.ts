import { Component, OnInit, ViewChild } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Supabase configuration (replace with your actual URL and key if different)
const supabaseUrl = 'https://eximxyncuxlgoqwvczmh.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

@Component({
  selector: 'app-doctor',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './doctor.component.html',
  styleUrl: './doctor.component.css'
})
export class DoctorComponent implements OnInit {
  doctorProfile = {
    full_name: '',
    specialization: '',
    license_number: '',
    contact_number: '',
    email: '',
    years_of_experience: null as number | null,
    about: ''
  };
  feedbackMessage: string = '';
  private supabase: SupabaseClient;

  constructor() {
     this.supabase = createClient(supabaseUrl, supabaseAnonKey);
  }

  async ngOnInit(): Promise<void> {
    // Fetch the user email from Supabase session and set it
    
   
  }

  async saveProfile() {
    console.log(this.doctorProfile);
    const { data } = await this.supabase.auth.getSession();
    this.doctorProfile.email = data?.session?.user?.email || '';
    this.feedbackMessage = '';

    // Validation: Check for missing required fields
    const missingFields = [];
    if (!this.doctorProfile.full_name) missingFields.push('Full Name');
    if (!this.doctorProfile.specialization) missingFields.push('Specialization');
    if (!this.doctorProfile.license_number) missingFields.push('License Number');
    if (!this.doctorProfile.contact_number) missingFields.push('Contact Number');
    if (!this.doctorProfile.email) missingFields.push('Email');
    if (
      this.doctorProfile.years_of_experience === null ||
      this.doctorProfile.years_of_experience === undefined ||
      this.doctorProfile.years_of_experience === 0
    ) missingFields.push('Years of Experience');
    if (!this.doctorProfile.about) missingFields.push('About');

    if (missingFields.length > 0) {
      this.feedbackMessage = `Please fill in the following required fields: ${missingFields.join(', ')}`;
      return;
    }

    // Prepare data
    const profileToSave = {
      ...this.doctorProfile,
      years_of_experience: this.doctorProfile.years_of_experience === null || this.doctorProfile.years_of_experience === undefined ? null : Number(this.doctorProfile.years_of_experience)
    };
    // Upsert into Supabase
    const { error } = await this.supabase
      .from('doctor_profiles')
      .upsert(profileToSave);
    if (error) {
      console.log(error);
      this.feedbackMessage = `Error saving profile: ${error.message}`;
    } else {
      this.feedbackMessage = 'Profile saved successfully!';
    }
  }
}