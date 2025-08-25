import SwiftUI

struct HouseListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var selectedStatus: HouseStatus? = nil

    @State private var selectedHouses: Set<UUID> = []
    @State private var showingMap = false
    @State private var showingRouteCreation = false
    @State private var isSelectionMode = false
    @State private var selectedSalespersonFilter: UUID? = nil
    @State private var houseAgeFilterDays: Int = 7  // Default to 1 week

    var filteredHouses: [House] {
        var houses = dataManager.houses

        if let status = selectedStatus {
            houses = houses.filter { $0.status == status }
        }

        if let salespersonId = selectedSalespersonFilter {
            houses = dataManager.getHousesForSalesperson(salespersonId)
        }

        houses = houses.filter { isHouseWithinAgeFilter($0) }

        return houses.sorted { (house1, house2) in
            // Since House doesn't have createdAt, sort by soldDate
            house1.soldDate > house2.soldDate
        }
    }

    private func isHouseWithinAgeFilter(_ house: House) -> Bool {
        guard let soldDate = Date.fromISO8601(house.soldDate) else { return false }
        let daysSinceSold = Calendar.current.dateComponents([.day], from: soldDate, to: Date()).day ?? 0
        return daysSinceSold <= houseAgeFilterDays
    }

    var body: some View {
        NavigationView {
            VStack {
                // Statistics cards
                HStack {
                    StatCard(title: "Total", value: "\(dataManager.totalHouses)", color: .blue)
                    StatCard(title: "New", value: "\(dataManager.newHouses)", color: .green)
                }
                .padding(.horizontal)

                // Status filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        FilterChip(title: "All", isSelected: selectedStatus == nil) {
                            selectedStatus = nil
                        }

                        ForEach(HouseStatus.allCases, id: \.self) { status in
                            FilterChip(title: status.displayName, isSelected: selectedStatus == status) {
                                selectedStatus = status
                            }
                        }
                    }
                    .padding(.horizontal)
                }

                // Salesperson filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        FilterChip(title: "All Salespeople", isSelected: selectedSalespersonFilter == nil) {
                            selectedSalespersonFilter = nil
                        }

                        ForEach(dataManager.salespeople, id: \.id) { salesperson in
                            FilterChip(title: salesperson.name, isSelected: selectedSalespersonFilter == salesperson.id) {
                                selectedSalespersonFilter = salesperson.id
                            }
                        }
                    }
                    .padding(.horizontal)
                }

                // Add filter section
                Section(header: Text("Filters")) {
                    Picker("Max Age (Days)", selection: $houseAgeFilterDays) {
                        Text("7 Days").tag(7)
                        Text("14 Days").tag(14)
                        Text("30 Days").tag(30)
                        Text("All").tag(Int.max)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }

                // Selection mode toolbar
                if isSelectionMode {
                    HStack {
                        Button("Cancel") {
                            isSelectionMode = false
                            selectedHouses.removeAll()
                        }
                        .foregroundColor(.red)

                        Spacer()

                        Text("\(selectedHouses.count) selected")
                            .font(.headline)
                            .foregroundColor(.blue)

                        Spacer()

                        Button("View on Map") {
                            showingMap = true
                        }
                        .disabled(selectedHouses.isEmpty)
                        .foregroundColor(selectedHouses.isEmpty ? .gray : .blue)

                        Button("Create Route") {
                            showingRouteCreation = true
                        }
                        .disabled(selectedHouses.count < 2)
                        .foregroundColor(selectedHouses.count < 2 ? .gray : .green)
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                    .background(Color(.systemGray6))
                }

                // House list
                List(filteredHouses) { house in
                    if isSelectionMode {
                        HouseRowView(
                            house: house,
                            isSelected: selectedHouses.contains(house.id),
                            isSelectionMode: isSelectionMode
                        ) {
                            if selectedHouses.contains(house.id) {
                                selectedHouses.remove(house.id)
                            } else {
                                selectedHouses.insert(house.id)
                            }
                        }
                    } else {
                        NavigationLink(destination: HouseDetailView(house: house).environmentObject(dataManager)) {
                            HouseRowView(
                                house: house,
                                isSelected: false,
                                isSelectionMode: false
                            ) {
                                // Empty closure since NavigationLink handles the navigation
                            }
                        }
                    }
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Houses")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(isSelectionMode ? "Done" : "Select") {
                        isSelectionMode.toggle()
                        if !isSelectionMode {
                            selectedHouses.removeAll()
                        }
                    }
                }
            }

            .sheet(isPresented: $showingMap) {
                NavigationView {
                    SelectedHousesMapView(selectedHouses: selectedHouses, allHouses: dataManager.houses)
                        .environmentObject(dataManager)
                        .navigationTitle("Selected Houses")
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .navigationBarTrailing) {
                                Button("Done") {
                                    showingMap = false
                                }
                            }
                        }
                }
            }
            .sheet(isPresented: $showingRouteCreation) {
                NavigationView {
                    RouteCreationView(selectedHouses: selectedHouses, allHouses: dataManager.houses)
                        .environmentObject(dataManager)
                        .navigationTitle("Create Route")
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .navigationBarTrailing) {
                                Button("Done") {
                                    showingRouteCreation = false
                                }
                            }
                        }
                }
            }
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let color: Color

    var body: some View {
        VStack {
            Text(value)
                .font(.title)
                .fontWeight(.bold)
                .foregroundColor(color)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(10)
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.blue : Color(.systemGray5))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(20)
        }
    }
}

struct HouseRowView: View {
    let house: House
    let isSelected: Bool
    let isSelectionMode: Bool
    let onTap: () -> Void
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
            HStack {
                // Selection indicator
                if isSelectionMode {
                    Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                        .foregroundColor(isSelected ? .blue : .gray)
                        .font(.title3)
                } else {
                    // Status indicator
                    Circle()
                        .fill(statusColor)
                        .frame(width: 12, height: 12)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(house.address)
                        .font(.headline)
                        .foregroundColor(.primary)

                    Text(house.contactName)
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    HStack {
                        Text(house.city)
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Spacer()

                        Text(house.formattedPrice)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.blue)
                    }

                    // Show assigned salesperson if any
                    if let assignedSalesperson = dataManager.getSalespersonForRegion(house.city) {
                        HStack {
                            Image(systemName: "person.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.purple)
                            Text("Assigned to \(assignedSalesperson.name)")
                                .font(.caption2)
                                .foregroundColor(.purple)
                        }
                    }
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text(house.status.displayName)
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(statusColor.opacity(0.2))
                        .foregroundColor(statusColor)
                        .cornerRadius(8)

                    HStack(spacing: 4) {
                        if house.fiberAvailable {
                            Image(systemName: "wifi")
                                .font(.caption2)
                                .foregroundColor(.green)
                        }

                        if house.adtDetected {
                            Image(systemName: "shield.fill")
                                .font(.caption2)
                                .foregroundColor(.orange)
                        }
                    }
                }
            }
            .padding(.vertical, 4)
            .background(isSelected && isSelectionMode ? Color.blue.opacity(0.1) : Color.clear)
            .contentShape(Rectangle())
            .onTapGesture {
                if isSelectionMode {
                    onTap()
                }
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
}

struct HouseListView_Previews: PreviewProvider {
    static var previews: some View {
        HouseListView()
            .environmentObject(DataManager())
    }
}

extension Date {
    static func fromISO8601(_ string: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: string)
    }
}
