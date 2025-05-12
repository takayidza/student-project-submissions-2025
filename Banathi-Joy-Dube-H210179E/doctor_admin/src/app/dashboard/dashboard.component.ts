import { Component, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { createClient } from '@supabase/supabase-js';
import { CommonModule } from '@angular/common';
import $ from 'jquery';
import { RemarkModule } from 'ngx-remark';

const supabaseUrl = 'https://eximxyncuxlgoqwvczmh.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4aW14eW5jdXhsZ29xd3Zjem1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MzM4NDEsImV4cCI6MjA2MTUwOTg0MX0.VpVEwWWm2NRUQrghAqhO5Pf5iuJU2cmZAao4-1b0NJc';
const supabase = createClient(supabaseUrl, supabaseAnonKey);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RemarkModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements AfterViewInit {
  @ViewChild('patientTable', { static: true }) table!: ElementRef;
  patientProfiles: any[] = [];
  conversation: any[] = [];
  activePrescriptionForm: string | null = null;
  selectedProfile: any = null;

  async ngOnInit() {
    const { data, error } = await supabase
      .from('patient_profile')
      .select('*');

    if (error) {
      console.error('Error fetching patient profiles:', error);
    } else {
      this.patientProfiles = data || [];
    }
  }

  async fetchConversation(email: string) {
    const { data, error } = await supabase
      .from('conversations')
      .select('*')
      .eq('email', email);

    if (error) {
      console.error('Error fetching conversation:', error);
    } else {
      console.log('Conversation data:', data);
      
      this.conversation = data || [];
    }
  }

  togglePrescriptionForm(profile: any) {
    this.activePrescriptionForm = this.activePrescriptionForm === profile.email ? null : profile.email;
    this.selectedProfile = this.activePrescriptionForm ? profile : null;
  }

  async submitPrescription(event: Event) {
    event.preventDefault();
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);

    const { data: { session } } = await supabase.auth.getSession();
    const email = session?.user?.email;

    if (!email) {
      console.error('No email found in the auth session.');
      return;
    }

    if (!this.selectedProfile) {
      console.error('No profile selected.');
      return;
    }

    const doctor_name = (await supabase
      .from('doctor_profiles')
      .select('full_name')
      .eq('email', email)
      .single()).data?.full_name || ''
    
    console.log("Doctor is ..." + doctor_name);

    const prescription = {
      email: this.selectedProfile.email,
      medication: formData.get('medication'),
      disease: formData.get('disease'),
      dosage: formData.get('dosage'),
      frequency: formData.get('frequency'),
      duration: formData.get('duration'),
      doctor_email: email,
      doctor_fullname: doctor_name,
      
    };

    const { error } = await supabase
      .from('prescription')
      .insert([prescription]);

    if (error) {
      console.error('Error submitting prescription:', error);
    } else {
      console.log('Prescription submitted successfully:', prescription);
    }
    // Display success message for 3 seconds
    const successMessage = document.createElement('div');
    successMessage.textContent = 'Prescription submitted successfully!';
    successMessage.style.color = 'green';
    form.appendChild(successMessage);

    setTimeout(() => {
      successMessage.remove();
      form.reset(); // Clear the form
      this.activePrescriptionForm = null; // Close the form after submission.
    }, 3000);
    
  }

  ngAfterViewInit() {
    ($(this.table.nativeElement) as any).DataTable();
  }
}
