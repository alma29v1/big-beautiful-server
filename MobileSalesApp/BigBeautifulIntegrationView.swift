import SwiftUI

struct BigBeautifulIntegrationView: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var showingContactForm = false
    @State private var showingEmailDashboard = false
    @State private var showingServerConfig = false
    @State private var addressToCheck = ""
    @State private var fiberCheckResult: FiberResponse?
    @State private var isCheckingFiber = false
    @State private var isSyncing = false

    var body: some View {
        ScrollView {
                VStack(spacing: 20) {
                    // Connection Status
                    ConnectionStatusCard()

                    // Sync Button with Timestamp
                    VStack(spacing: 8) {
                        Button(action: syncData) {
                            HStack {
                                if isSyncing {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                } else {
                                    Image(systemName: "arrow.clockwise")
                                }
                                Text(isSyncing ? "Syncing..." : "Sync Data (Auto-Fallback)")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(isSyncing ? Color.gray : Color.green)
                            .cornerRadius(12)
                        }
                        .disabled(isSyncing)

                        if let lastSync = dataManager.lastSyncTimestamp {
                            Text("Last synced: \(lastSync, style: .relative) ago")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        } else {
                            Text("Never synced")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        // Show current connection status
                        Text(dataManager.bigBeautifulAPIClient.connectionStatus)
                            .font(.caption)
                            .foregroundColor(dataManager.isBigBeautifulConnected ? .green : .orange)
                            .fontWeight(.medium)
                    }
                    .padding(.horizontal)

                    // Email Campaign Summary
                    EmailCampaignSummaryCard()

                    // Analytics Dashboard
                    if let analytics = dataManager.analytics {
                        AnalyticsCard(analytics: analytics)
                    }

                    // AT&T Fiber Checker
                    FiberCheckerCard(
                        addressToCheck: $addressToCheck,
                        fiberCheckResult: $fiberCheckResult,
                        isCheckingFiber: $isCheckingFiber,
                        onCheckFiber: checkATTFiber
                    )

                    // Contacts List
                    ContactsListCard(contacts: dataManager.contacts)

                    // Action Buttons
                    VStack(spacing: 12) {
                        Button(action: { showingEmailDashboard = true }) {
                            HStack {
                                Image(systemName: "chart.bar.fill")
                                Text("Sales Analytics Dashboard")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.purple)
                            .cornerRadius(12)
                        }

                        Button(action: { showingContactForm = true }) {
                            HStack {
                                Image(systemName: "person.badge.plus")
                                Text("Add New Contact")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .cornerRadius(12)
                        }

                        Button(action: { showingServerConfig = true }) {
                            HStack {
                                Image(systemName: "gear")
                                Text("Server Configuration")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.orange)
                            .cornerRadius(12)
                        }
                    }
                    .padding(.horizontal)
                }
                .padding()
            }
            .navigationTitle("Big Beautiful Program")
            .sheet(isPresented: $showingContactForm) {
                AddContactView()
                    .environmentObject(dataManager)
            }
            .sheet(isPresented: $showingEmailDashboard) {
                EmailCampaignDashboard()
                    .environmentObject(dataManager)
            }
            .sheet(isPresented: $showingServerConfig) {
                ServerConfigurationView()
                    .environmentObject(dataManager)
            }
        }

    private func checkATTFiber() {
        guard !addressToCheck.isEmpty else { return }

        isCheckingFiber = true
        Task {
            let result = await dataManager.checkATTFiberForAddress(addressToCheck)
            await MainActor.run {
                fiberCheckResult = result
                isCheckingFiber = false
            }
        }
    }

    private func syncData() {
        isSyncing = true
        Task {
            await dataManager.refreshBigBeautifulData()
            await MainActor.run {
                isSyncing = false
            }
        }
    }
}

struct EmailCampaignSummaryCard: View {
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .foregroundColor(.purple)
                    .font(.title2)

                Text("Rolling Sales Data")
                    .font(.headline)

                Spacer()

                Text("Weekly")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.purple.opacity(0.2))
                    .foregroundColor(.purple)
                    .cornerRadius(8)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Sales Performance")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text("Tap 'Sync Data' to load the latest rolling sales data from Big Beautiful Program.")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .italic()
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct ConnectionStatusCard: View {
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: dataManager.isBigBeautifulConnected ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(dataManager.isBigBeautifulConnected ? .green : .red)
                    .font(.title2)

                Text("Big Beautiful Program Connection")
                    .font(.headline)

                Spacer()

                if dataManager.isBigBeautifulConnected {
                    Text("Connected")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.2))
                        .foregroundColor(.green)
                        .cornerRadius(8)
                } else {
                    Text("Disconnected")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.red.opacity(0.2))
                        .foregroundColor(.red)
                        .cornerRadius(8)
                }
            }

                        VStack(alignment: .leading, spacing: 4) {
                Text("Current Server: \(dataManager.bigBeautifulAPIClient.baseURL)")
                    .font(.caption)
                    .foregroundColor(.green)

                Text("Status: \(dataManager.bigBeautifulAPIClient.connectionStatus)")
                    .font(.caption)
                    .foregroundColor(dataManager.isBigBeautifulConnected ? .green : .orange)

                if dataManager.isBigBeautifulConnected {
                    Text("✅ API Key: \(String(dataManager.bigBeautifulAPIClient.apiKey.prefix(8)))...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                } else {
                    Text("🔄 Auto-fallback will try multiple servers")
                        .font(.caption2)
                        .foregroundColor(.blue)
                        .italic()
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct AnalyticsCard: View {
    let analytics: AnalyticsResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Analytics Dashboard")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                                    BigBeautifulStatCard(title: "Total Contacts", value: "\(analytics.totalContacts)", color: .blue)
                    BigBeautifulStatCard(title: "Fiber Contacts", value: "\(analytics.fiberContacts)", color: .green)
                    BigBeautifulStatCard(title: "Recent Contacts", value: "\(analytics.recentContacts)", color: .orange)
                    BigBeautifulStatCard(title: "Conversion Rate", value: "\(Int(analytics.conversionRate))%", color: .purple)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Top Cities")
                    .font(.subheadline)
                    .fontWeight(.semibold)

                ForEach(analytics.topCities.prefix(3), id: \.city) { city in
                    HStack {
                        Text(city.city)
                        Spacer()
                        Text("\(city.count) contacts")
                            .foregroundColor(.secondary)
                    }
                    .font(.caption)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct FiberCheckerCard: View {
    @Binding var addressToCheck: String
    @Binding var fiberCheckResult: FiberResponse?
    @Binding var isCheckingFiber: Bool
    let onCheckFiber: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("AT&T Fiber Checker")
                .font(.headline)

            TextField("Enter address to check", text: $addressToCheck)
                .textFieldStyle(RoundedBorderTextFieldStyle())

            Button(action: onCheckFiber) {
                HStack {
                    if isCheckingFiber {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "wifi")
                    }
                    Text(isCheckingFiber ? "Checking..." : "Check Fiber Availability")
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .cornerRadius(12)
            }
            .disabled(addressToCheck.isEmpty || isCheckingFiber)

            if let result = fiberCheckResult {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: result.fiberAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(result.fiberAvailable ? .green : .red)
                        Text(result.fiberAvailable ? "Fiber Available" : "Fiber Not Available")
                            .fontWeight(.semibold)
                    }

                    if result.fiberAvailable {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Speed Tiers:")
                                .font(.caption)
                                .fontWeight(.semibold)
                            ForEach(result.speedTiers, id: \.self) { speed in
                                Text("• \(speed)")
                                    .font(.caption)
                            }
                        }

                        if !result.promotionalOffers.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Promotional Offers:")
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                ForEach(result.promotionalOffers, id: \.speed) { offer in
                                    Text("• \(offer.speed) - \(offer.price) (\(offer.term))")
                                        .font(.caption)
                                }
                            }
                        }
                    }
                }
                .padding()
                .background(Color(.systemGray6).opacity(0.3))
                .cornerRadius(8)
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct ContactsListCard: View {
    let contacts: [Contact]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Contacts (\(contacts.count))")
                .font(.headline)

            if contacts.isEmpty {
                Text("No contacts loaded")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(contacts.prefix(5)) { contact in
                        ContactRow(contact: contact)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct ContactRow: View {
    let contact: Contact

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(contact.ownerName)
                    .font(.subheadline)
                    .fontWeight(.semibold)

                Spacer()

                if contact.fiberAvailable {
                    Image(systemName: "wifi")
                        .foregroundColor(.green)
                        .font(.caption)
                }
            }

            Text(contact.address)
                .font(.caption)
                .foregroundColor(.secondary)

            Text("\(contact.city), \(contact.state) \(contact.zipCode)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct AddContactView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode

    @State private var address = ""
    @State private var city = ""
    @State private var state = ""
    @State private var zipCode = ""
    @State private var ownerName = ""
    @State private var ownerEmail = ""
    @State private var ownerPhone = ""
    @State private var fiberAvailable = false
    @State private var isCreating = false

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Address Information")) {
                    TextField("Address", text: $address)
                    TextField("City", text: $city)
                    TextField("State", text: $state)
                    TextField("ZIP Code", text: $zipCode)
                }

                Section(header: Text("Owner Information")) {
                    TextField("Owner Name", text: $ownerName)
                    TextField("Owner Email", text: $ownerEmail)
                    TextField("Owner Phone", text: $ownerPhone)
                }

                Section(header: Text("Fiber Information")) {
                    Toggle("Fiber Available", isOn: $fiberAvailable)
                }

                Section {
                    Button(action: createContact) {
                        HStack {
                            if isCreating {
                                ProgressView()
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "person.badge.plus")
                            }
                            Text(isCreating ? "Creating..." : "Create Contact")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .disabled(address.isEmpty || city.isEmpty || state.isEmpty || zipCode.isEmpty || ownerName.isEmpty || isCreating)
                }
            }
            .navigationTitle("Add Contact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
        }
    }

    private func createContact() {
        guard !address.isEmpty && !city.isEmpty && !state.isEmpty && !zipCode.isEmpty && !ownerName.isEmpty else { return }

        isCreating = true
        Task {
            let contact = await dataManager.createContactInBigBeautiful(
                address: address,
                city: city,
                state: state,
                zipCode: zipCode,
                ownerName: ownerName,
                ownerEmail: ownerEmail,
                ownerPhone: ownerPhone,
                fiberAvailable: fiberAvailable
            )

            await MainActor.run {
                isCreating = false
                if contact != nil {
                    presentationMode.wrappedValue.dismiss()
                }
            }
        }
    }
}

struct BigBeautifulStatCard: View {
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
