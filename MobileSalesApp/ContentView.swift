import SwiftUI

struct ContentView: View {
    @StateObject private var dataManager = DataManager()

    var body: some View {
        TabView {
            MapView()
                .environmentObject(dataManager)
                .tabItem {
                    Image(systemName: "map.fill")
                    Text("Map")
                }

            NavigationView {
                HouseListView()
                    .environmentObject(dataManager)
            }
            .tabItem {
                Image(systemName: "house.fill")
                Text("Houses")
            }

            NavigationView {
                IncidentListView()
                    .environmentObject(dataManager)
            }
            .tabItem {
                Image(systemName: "exclamationmark.triangle.fill")
                Text("Incidents")
            }

            NavigationView {
                RouteListView()
                    .environmentObject(dataManager)
            }
            .tabItem {
                Image(systemName: "map.fill")
                Text("Routes")
            }

            NavigationView {
                BigBeautifulIntegrationView()
                    .environmentObject(dataManager)
            }
            .tabItem {
                Image(systemName: "server.rack")
                Text("Big Beautiful")
            }

            NavigationView {
                RegionAssignmentView()
                    .environmentObject(dataManager)
            }
            .tabItem {
                Image(systemName: "person.2.circle")
                Text("Regions")
            }
        }
        .accentColor(.blue)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
