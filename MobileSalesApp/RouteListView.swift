import SwiftUI
import MapKit

struct RouteListView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var showingCreateRoute = false
    
    var body: some View {
        VStack {
                // Statistics
                HStack {
                    StatCard(title: "Routes", value: "\(dataManager.totalRoutes)", color: .blue)
                    StatCard(title: "Active", value: "\(dataManager.routes.count)", color: .green)
                }
                .padding(.horizontal)
                
                // Route list
                List(dataManager.routes) { route in
                    RouteRowView(route: route)
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Routes")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingCreateRoute = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreateRoute) {
                CreateRouteView()
                    .environmentObject(dataManager)
            }
        }
    }

struct RouteRowView: View {
    let route: Route
    @EnvironmentObject var dataManager: DataManager
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(route.name)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("\(route.houseCount) houses")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text(route.estimatedTime)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.blue)
                    
                    Text("Est. Time")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            HStack {
                Image(systemName: "person.fill")
                    .font(.caption)
                    .foregroundColor(.blue)
                
                Text(getSalespersonName())
                    .font(.caption)
                    .foregroundColor(.blue)
                
                Spacer()
                
                Button("Export to Maps") {
                    exportRouteToMaps()
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func getSalespersonName() -> String {
        // In a real app, you'd get this from the data manager
        return "Salesperson"
    }
    
    private func exportRouteToMaps() {
        // Get all houses in this route
        let routeHouses = dataManager.houses.filter { route.houseIds.contains($0.id) }
        
        // Create map items for each house
        let mapItems = routeHouses.map { house in
            let placemark = MKPlacemark(coordinate: house.coordinate)
            let mapItem = MKMapItem(placemark: placemark)
            mapItem.name = house.address
            return mapItem
        }
        
        // Open in Apple Maps with all locations
        MKMapItem.openMaps(with: mapItems, launchOptions: [
            MKLaunchOptionsDirectionsModeKey: MKLaunchOptionsDirectionsModeDriving
        ])
    }
}

struct CreateRouteView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode
    @State private var routeName = ""
    @State private var selectedSalesperson: SalesPerson?
    @State private var selectedHouses: Set<UUID> = []
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Route Details")) {
                    TextField("Route Name", text: $routeName)
                    
                    Picker("Salesperson", selection: $selectedSalesperson) {
                        Text("Select Salesperson").tag(nil as SalesPerson?)
                        ForEach(dataManager.salespeople) { salesperson in
                            Text(salesperson.name).tag(salesperson as SalesPerson?)
                        }
                    }
                }
                
                Section(header: Text("Select Houses")) {
                    ForEach(dataManager.houses) { house in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(house.address)
                                    .font(.subheadline)
                                Text(house.city)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            if selectedHouses.contains(house.id) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.blue)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture {
                            if selectedHouses.contains(house.id) {
                                selectedHouses.remove(house.id)
                            } else {
                                selectedHouses.insert(house.id)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Create Route")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Create") {
                        createRoute()
                    }
                    .disabled(routeName.isEmpty || selectedSalesperson == nil || selectedHouses.isEmpty)
                }
            }
        }
    }
    
    private func createRoute() {
        guard let salesperson = selectedSalesperson else { return }
        
        let route = Route(
            name: routeName,
            salespersonId: salesperson.id,
            houseIds: Array(selectedHouses)
        )
        
        dataManager.addRoute(route)
        presentationMode.wrappedValue.dismiss()
    }
}

struct RouteListView_Previews: PreviewProvider {
    static var previews: some View {
        RouteListView()
            .environmentObject(DataManager())
    }
}
