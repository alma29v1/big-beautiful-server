import SwiftUI

struct ContentView: View {
    @StateObject private var dataManager = DataManager()
    @State private var userRole: UserRole? = nil  // nil means not logged in

    var body: some View {
        if userRole == nil {
            LoginView(onLogin: { role in
                self.userRole = role
            })
        } else {
            TabView {
                // Common tabs
                MapView().environmentObject(dataManager).tabItem { Image(systemName: "map.fill"); Text("Map") }
                NavigationView { HouseListView().environmentObject(dataManager) }.tabItem { Image(systemName: "house.fill"); Text("Houses") }
                NavigationView { IncidentListView().environmentObject(dataManager) }.tabItem { Image(systemName: "exclamationmark.triangle.fill"); Text("Incidents") }
                NavigationView { RouteListView().environmentObject(dataManager) }.tabItem { Image(systemName: "map.fill"); Text("Routes") }

                // Manager-only tabs
                if userRole == .manager {
                    NavigationView { BigBeautifulIntegrationView().environmentObject(dataManager) }.tabItem { Image(systemName: "server.rack"); Text("Big Beautiful") }
                    NavigationView { RegionAssignmentView().environmentObject(dataManager) }.tabItem { Image(systemName: "person.2.circle"); Text("Regions") }
                    // Add Marketplace tab here later
                }
            }
            .accentColor(.blue)
        }
    }
}

enum UserRole {
    case manager
    case employee
}

struct LoginView: View {
    let onLogin: (UserRole) -> Void
    @State private var selectedRole: UserRole?

    var body: some View {
        VStack {
            Text("Select Role")
                .font(.largeTitle)

            Picker("Role", selection: $selectedRole) {
                Text("Manager").tag(UserRole.manager as UserRole?)
                Text("Employee").tag(UserRole.employee as UserRole?)
            }
            .pickerStyle(SegmentedPickerStyle())

            Button("Login") {
                if let role = selectedRole {
                    onLogin(role)
                }
            }
            .disabled(selectedRole == nil)
        }
        .padding()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
