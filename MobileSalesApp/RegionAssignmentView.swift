import SwiftUI

struct RegionAssignmentView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode
    @State private var selectedCity: String = ""
    @State private var selectedSalespersonId: UUID?

    var body: some View {
        VStack(spacing: 20) {
                // Assignment Section
                VStack(alignment: .leading, spacing: 12) {
                    Text("Assign Region to Salesperson")
                        .font(.headline)
                        .fontWeight(.semibold)

                    // City Picker
                    Picker("Select City", selection: $selectedCity) {
                        Text("Select a city").tag("")
                        ForEach(dataManager.getAvailableCities(), id: \.self) { city in
                            Text(city).tag(city)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                    .padding()
                    .background(Color(.systemGray6).opacity(0.3))
                    .cornerRadius(8)

                    // Salesperson Picker
                    if !selectedCity.isEmpty {
                        Picker("Select Salesperson", selection: $selectedSalespersonId) {
                            Text("Select a salesperson").tag(nil as UUID?)
                            ForEach(dataManager.salespeople, id: \.id) { salesperson in
                                Text(salesperson.name).tag(salesperson.id as UUID?)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                        .padding()
                        .background(Color(.systemGray6).opacity(0.3))
                        .cornerRadius(8)

                        // Assign Button
                        Button(action: assignRegion) {
                            HStack {
                                Image(systemName: "person.badge.plus")
                                Text("Assign \(selectedCity) to Salesperson")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .cornerRadius(8)
                        }
                        .disabled(selectedSalespersonId == nil)
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Current Assignments
                VStack(alignment: .leading, spacing: 12) {
                    Text("Current Assignments")
                        .font(.headline)
                        .fontWeight(.semibold)

                    if dataManager.regionAssignments.isEmpty {
                        Text("No regions assigned yet")
                            .foregroundColor(.secondary)
                            .italic()
                    } else {
                        ForEach(dataManager.getAssignedCities(), id: \.self) { city in
                            if let salesperson = dataManager.getSalespersonForRegion(city) {
                                HStack {
                                    VStack(alignment: .leading) {
                                        Text(city)
                                            .fontWeight(.medium)
                                        Text(salesperson.name)
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }

                                    Spacer()

                                    Button(action: { unassignRegion(city) }) {
                                        Image(systemName: "xmark.circle.fill")
                                            .foregroundColor(.red)
                                    }
                                }
                                .padding()
                                .background(Color(.systemGray6).opacity(0.3))
                                .cornerRadius(8)
                            }
                        }
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Statistics
                VStack(alignment: .leading, spacing: 12) {
                    Text("Statistics")
                        .font(.headline)
                        .fontWeight(.semibold)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 12) {
                        RegionStatCard(title: "Assigned Cities", value: "\(dataManager.getAssignedCities().count)", color: .blue)
                        RegionStatCard(title: "Unassigned Houses", value: "\(dataManager.getUnassignedHouses().count)", color: .orange)
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                Spacer()
            }
            .padding()
            .navigationTitle("Region Assignment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
        }

    private func assignRegion() {
        guard let salespersonId = selectedSalespersonId else { return }
        dataManager.assignRegion(selectedCity, to: salespersonId)
        selectedCity = ""
        selectedSalespersonId = nil
    }

    private func unassignRegion(_ city: String) {
        dataManager.unassignRegion(city)
    }
}

struct RegionStatCard: View {
    let title: String
    let value: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}

#Preview {
    RegionAssignmentView()
        .environmentObject(DataManager())
}
