import SwiftUI

struct VisitRecordView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode
    let house: House
    
    @State private var selectedSalesperson: SalesPerson?
    @State private var visitStatus: VisitStatus = .contacted
    @State private var notes = ""
    @State private var followUpDate: Date = Date().addingTimeInterval(7*24*60*60)
    @State private var includeFollowUp = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("House Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(house.address)
                            .font(.headline)
                        Text(house.fullAddress)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section(header: Text("Visit Details")) {
                    Picker("Salesperson", selection: $selectedSalesperson) {
                        Text("Select Salesperson").tag(nil as SalesPerson?)
                        ForEach(dataManager.salespeople) { salesperson in
                            Text(salesperson.name).tag(salesperson as SalesPerson?)
                        }
                    }
                    
                    Picker("Status", selection: $visitStatus) {
                        ForEach(VisitStatus.allCases, id: \.self) { status in
                            Text(status.displayName).tag(status)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                Section(header: Text("Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                }
                
                Section(header: Text("Follow Up")) {
                    Toggle("Schedule Follow Up", isOn: $includeFollowUp)
                    
                    if includeFollowUp {
                        DatePicker("Follow Up Date", selection: $followUpDate, displayedComponents: .date)
                    }
                }
            }
            .navigationTitle("Record Visit")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveVisit()
                    }
                    .disabled(selectedSalesperson == nil)
                }
            }
        }
    }
    
    private func saveVisit() {
        guard let salesperson = selectedSalesperson else { return }
        
        let visit = Visit(
            houseId: house.id,
            salespersonId: salesperson.id,
            status: visitStatus,
            notes: notes,
            followUpDate: includeFollowUp ? followUpDate : nil
        )
        
        dataManager.addVisit(visit)
        presentationMode.wrappedValue.dismiss()
    }
}

struct VisitRecordView_Previews: PreviewProvider {
    static var previews: some View {
        VisitRecordView(house: House(
            address: "123 Main St",
            city: "Wilmington",
            state: "NC",
            zipCode: "28401",
            latitude: 34.2257,
            longitude: -77.9447,
            soldDate: "2024-01-15",
            price: 250000,
            contactName: "John Smith",
            contactEmail: "john@email.com",
            contactPhone: "910-555-0101",
            fiberAvailable: true,
            adtDetected: false
        ))
        .environmentObject(DataManager())
    }
}
