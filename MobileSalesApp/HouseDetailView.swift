import SwiftUI
import MapKit

struct HouseDetailView: View {
    @EnvironmentObject var dataManager: DataManager
    @State var house: House
    @State private var showingEditSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                                // Header
                VStack(alignment: .leading, spacing: 8) {
                    Text(house.address)
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(house.fullAddress)
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    HStack {
                        Text(house.status.displayName)
                            .font(.caption)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(statusColor.opacity(0.2))
                            .foregroundColor(statusColor)
                            .cornerRadius(12)

                        Spacer()

                        Text(house.formattedPrice)
                            .font(.headline)
                            .foregroundColor(.blue)
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Contact Information
                VStack(alignment: .leading, spacing: 12) {
                    Text("Contact Information")
                        .font(.headline)

                    InfoRow(title: "Name", value: house.contactName)
                    InfoRow(title: "Email", value: house.contactEmail)
                    InfoRow(title: "Phone", value: house.contactPhone)
                    InfoRow(title: "Sold Date", value: house.soldDate)
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Property Details
                VStack(alignment: .leading, spacing: 12) {
                    Text("Property Details")
                        .font(.headline)

                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Fiber Available")
                                .font(.subheadline)
                                .foregroundColor(.secondary)

                            HStack {
                                Image(systemName: house.fiberAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(house.fiberAvailable ? .green : .red)
                                Text(house.fiberAvailable ? "Yes" : "No")
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                            }
                        }

                        Spacer()

                        VStack(alignment: .trailing, spacing: 4) {
                            Text("ADT Detected")
                                .font(.subheadline)
                                .foregroundColor(.secondary)

                            HStack {
                                Text(house.adtDetected ? "Yes" : "No")
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                Image(systemName: house.adtDetected ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(house.adtDetected ? .orange : .red)
                            }
                        }
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Navigation Button
                VStack(alignment: .leading, spacing: 12) {
                    Text("Navigation")
                        .font(.headline)

                    Button(action: {
                        openInMaps()
                    }) {
                        HStack {
                            Image(systemName: "location.fill")
                                .foregroundColor(.white)
                            Text("Navigate to House")
                                .fontWeight(.medium)
                                .foregroundColor(.white)
                            Spacer()
                            Image(systemName: "arrow.up.right")
                                .foregroundColor(.white)
                        }
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(10)
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(12)

                // Notes
                if !house.notes.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Notes")
                            .font(.headline)

                        Text(house.notes)
                            .font(.body)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(Color(.systemGray6).opacity(0.3))
                    .cornerRadius(12)
                }

                // Action Buttons
                VStack(spacing: 12) {
                    Button(action: {
                        showingEditSheet = true
                    }) {
                        HStack {
                            Image(systemName: "pencil")
                            Text("Edit House")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(.systemGray5))
                        .foregroundColor(.primary)
                        .cornerRadius(12)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("House Details")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showingEditSheet) {
            EditHouseView(house: $house)
                .environmentObject(dataManager)
        }
    }

    private var statusColor: Color {
        switch house.status {
        case .new:
            return .green
        case .contacted:
            return .orange
        case .interested:
            return .blue
        case .notHome:
            return .yellow
        case .notInterested:
            return .red
        case .sold:
            return .purple
        }
    }

    private func openInMaps() {
        let coordinate = CLLocationCoordinate2D(latitude: house.latitude, longitude: house.longitude)
        let mapItem = MKMapItem(placemark: MKPlacemark(coordinate: coordinate))
        mapItem.name = house.address
        mapItem.openInMaps(launchOptions: [
            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving
        ])
    }
}

struct InfoRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)

            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)

            Spacer()
        }
    }
}



struct EditHouseView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode
    @Binding var house: House
    @State private var status: HouseStatus
    @State private var notes: String

    init(house: Binding<House>) {
        self._house = house
        self._status = State(initialValue: house.wrappedValue.status)
        self._notes = State(initialValue: house.wrappedValue.notes)
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Status")) {
                    Picker("Status", selection: $status) {
                        ForEach(HouseStatus.allCases, id: \.self) { status in
                            Text(status.displayName).tag(status)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }

                Section(header: Text("Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle("Edit House")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        house.status = status
                        house.notes = notes
                        dataManager.updateHouse(house)
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
        }
    }
}

struct HouseDetailView_Previews: PreviewProvider {
    static var previews: some View {
        HouseDetailView(house: House(
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
