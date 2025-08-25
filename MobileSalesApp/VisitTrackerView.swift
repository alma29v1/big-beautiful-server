import SwiftUI

struct VisitTrackerView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode
    
    let address: String
    
    @State private var visitStage: VisitStage = .beforeVisit
    @State private var contactStatus = "new"
    @State private var visitNotes = ""
    @State private var selectedProducts: Set<String> = []
    @State private var appointmentScheduled = false
    @State private var followUpDate = Date()
    @State private var isUpdating = false
    @State private var customerName = ""
    @State private var customerPhone = ""
    @State private var customerEmail = ""
    
    private let visitStages: [VisitStage] = [.beforeVisit, .atDoor, .afterVisit]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Progress Header
                VStack(spacing: 16) {
                    Text("Visit Progress")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text(address)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    // Progress Indicator
                    HStack(spacing: 0) {
                        ForEach(visitStages, id: \.self) { stage in
                            HStack(spacing: 0) {
                                Circle()
                                    .fill(stage.rawValue <= visitStage.rawValue ? Color.blue : Color.gray.opacity(0.3))
                                    .frame(width: 20, height: 20)
                                    .overlay(
                                        Text("\(stage.rawValue + 1)")
                                            .font(.caption)
                                            .fontWeight(.bold)
                                            .foregroundColor(.white)
                                    )
                                
                                if stage != visitStages.last {
                                    Rectangle()
                                        .fill(stage.rawValue < visitStage.rawValue ? Color.blue : Color.gray.opacity(0.3))
                                        .frame(height: 2)
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                    
                    // Stage Labels
                    HStack {
                        ForEach(visitStages, id: \.self) { stage in
                            Text(stage.displayName)
                                .font(.caption)
                                .fontWeight(stage == visitStage ? .bold : .regular)
                                .foregroundColor(stage == visitStage ? .blue : .secondary)
                                .frame(maxWidth: .infinity)
                        }
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                
                // Stage Content
                ScrollView {
                    VStack(spacing: 20) {
                        switch visitStage {
                        case .beforeVisit:
                            BeforeVisitContent()
                        case .atDoor:
                            AtDoorContent()
                        case .afterVisit:
                            AfterVisitContent()
                        }
                    }
                    .padding()
                }
                
                // Navigation Buttons
                HStack(spacing: 16) {
                    if visitStage != .beforeVisit {
                        Button("Previous") {
                            withAnimation {
                                visitStage = VisitStage(rawValue: visitStage.rawValue - 1) ?? .beforeVisit
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.gray.opacity(0.2))
                        .cornerRadius(8)
                    }
                    
                    Button(visitStage == .afterVisit ? "Complete Visit" : "Next") {
                        if visitStage == .afterVisit {
                            completeVisit()
                        } else {
                            withAnimation {
                                visitStage = VisitStage(rawValue: visitStage.rawValue + 1) ?? .afterVisit
                            }
                        }
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(visitStage == .afterVisit ? Color.green : Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                    .disabled(isUpdating)
                }
                .padding()
            }
            .navigationTitle("Visit Tracker")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }
    
    @ViewBuilder
    private func BeforeVisitContent() -> some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Pre-Visit Checklist", icon: "checklist")
            
            ChecklistItem(text: "Review incident context and talking points", isCompleted: true)
            ChecklistItem(text: "Check product recommendations", isCompleted: true)
            ChecklistItem(text: "Prepare objection responses", isCompleted: true)
            ChecklistItem(text: "Ensure you have business cards and materials", isCompleted: false)
            
            SectionHeader(title: "Visit Preparation", icon: "person.fill.checkmark")
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Best Time to Visit")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text("• Weekday evenings (5-7 PM)")
                Text("• Weekend afternoons (1-4 PM)")
                Text("• Avoid meal times and early mornings")
            }
            .font(.body)
            .foregroundColor(.secondary)
            .padding()
            .background(Color.blue.opacity(0.1))
            .cornerRadius(8)
        }
    }
    
    @ViewBuilder
    private func AtDoorContent() -> some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "At the Door", icon: "door.left.hand.open")
            
            VStack(alignment: .leading, spacing: 8) {
                Text("First Impression Tips")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                
                Text("• Smile and make eye contact")
                Text("• Stand slightly to the side of the door")
                Text("• Have your badge/ID visible")
                Text("• Keep a respectful distance")
            }
            .font(.body)
            .foregroundColor(.secondary)
            .padding()
            .background(Color.green.opacity(0.1))
            .cornerRadius(8)
            
            SectionHeader(title: "Contact Information", icon: "person.crop.circle")
            
            Group {
                TextField("Customer Name", text: $customerName)
                TextField("Phone Number", text: $customerPhone)
                    .keyboardType(.phonePad)
                TextField("Email (optional)", text: $customerEmail)
                    .keyboardType(.emailAddress)
            }
            .textFieldStyle(RoundedBorderTextFieldStyle())
            
            SectionHeader(title: "Initial Notes", icon: "note.text")
            
            TextEditor(text: $visitNotes)
                .frame(height: 100)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )
        }
    }
    
    @ViewBuilder
    private func AfterVisitContent() -> some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Visit Outcome", icon: "checkmark.circle")
            
            Picker("Contact Status", selection: $contactStatus) {
                Text("Interested").tag("interested")
                Text("Not Home").tag("not_home")
                Text("Not Interested").tag("not_interested")
                Text("Appointment Scheduled").tag("appointment")
                Text("Follow Up Required").tag("follow_up")
            }
            .pickerStyle(SegmentedPickerStyle())
            
            if contactStatus == "interested" || contactStatus == "appointment" {
                SectionHeader(title: "Products Discussed", icon: "shield.checkered")
                
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(productOptions, id: \.self) { product in
                        Button(action: {
                            if selectedProducts.contains(product) {
                                selectedProducts.remove(product)
                            } else {
                                selectedProducts.insert(product)
                            }
                        }) {
                            HStack {
                                Image(systemName: selectedProducts.contains(product) ? "checkmark.square.fill" : "square")
                                    .foregroundColor(selectedProducts.contains(product) ? .blue : .gray)
                                
                                Text(product)
                                    .foregroundColor(.primary)
                                
                                Spacer()
                            }
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            
            if contactStatus == "appointment" {
                Toggle("Appointment Scheduled", isOn: $appointmentScheduled)
                
                if appointmentScheduled {
                    DatePicker("Follow-up Date", selection: $followUpDate, displayedComponents: [.date, .hourAndMinute])
                }
            }
            
            SectionHeader(title: "Visit Notes", icon: "note.text")
            
            TextEditor(text: $visitNotes)
                .frame(height: 120)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )
                .overlay(
                    Text(visitNotes.isEmpty ? "Record details about the visit, customer responses, next steps..." : "")
                        .foregroundColor(.gray)
                        .padding()
                        .allowsHitTesting(false),
                    alignment: .topLeading
                )
        }
    }
    
    private var productOptions: [String] {
        ["Security System Package", "Door/Window Sensors", "Security Cameras", "Motion Detectors", "Smart Locks", "Smoke/Fire Detectors", "Carbon Monoxide Detector"]
    }
    
    private func completeVisit() {
        isUpdating = true
        
        let statusUpdate = ContactStatusUpdate(
            contactId: nil,
            address: address,
            status: contactStatus,
            notes: visitNotes,
            salesPersonName: "Current User" // TODO: Get from user session
        )
        
        Task {
            do {
                let response = try await dataManager.bigBeautifulAPIClient.updateContactStatus(statusUpdate)
                
                await MainActor.run {
                    self.isUpdating = false
                    if response.success {
                        self.presentationMode.wrappedValue.dismiss()
                    }
                }
            } catch {
                await MainActor.run {
                    self.isUpdating = false
                    print("Failed to update contact status: \(error)")
                }
            }
        }
    }
}

// MARK: - Supporting Views and Models

enum VisitStage: Int, CaseIterable {
    case beforeVisit = 0
    case atDoor = 1
    case afterVisit = 2
    
    var displayName: String {
        switch self {
        case .beforeVisit: return "Before"
        case .atDoor: return "At Door"
        case .afterVisit: return "After"
        }
    }
}

struct SectionHeader: View {
    let title: String
    let icon: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.blue)
            
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            Spacer()
        }
        .padding(.top, 8)
    }
}

struct ChecklistItem: View {
    let text: String
    let isCompleted: Bool
    
    var body: some View {
        HStack {
            Image(systemName: isCompleted ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isCompleted ? .green : .gray)
            
            Text(text)
                .foregroundColor(isCompleted ? .secondary : .primary)
                .strikethrough(isCompleted)
            
            Spacer()
        }
        .padding(.vertical, 2)
    }
}

struct VisitTrackerView_Previews: PreviewProvider {
    static var previews: some View {
        VisitTrackerView(address: "123 Main Street, Anytown, ST 12345")
            .environmentObject(DataManager())
    }
}
