import SwiftUI

struct ServerConfigurationView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode

    @State private var serverHost: String
    @State private var serverPort: String
    @State private var isTestingConnection = false
    @State private var testResult: String = ""
    @State private var showingAlert = false

    init() {
        let client = BigBeautifulAPIClient()
        _serverHost = State(initialValue: client.serverHost)
        _serverPort = State(initialValue: client.serverPort)
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Server Configuration")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Server Host/IP")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter server host or IP", text: $serverHost)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .placeholder(when: serverHost.isEmpty) {
                                Text("192.168.84.130 (Production)")
                                    .foregroundColor(.gray)
                            }
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Server Port")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter port number", text: $serverPort)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.numberPad)
                    }
                }

                Section(header: Text("Current Configuration")) {
                    HStack {
                        Text("URL:")
                        Spacer()
                        Text("http://\(serverHost):\(serverPort)/api")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("Status:")
                        Spacer()
                        Text(dataManager.isBigBeautifulConnected ? "Connected" : "Disconnected")
                            .foregroundColor(dataManager.isBigBeautifulConnected ? .green : .red)
                    }
                }

                Section(header: Text("Connection Test")) {
                    VStack(spacing: 12) {
                        Button(action: testConnection) {
                            HStack {
                                if isTestingConnection {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                } else {
                                    Image(systemName: "wifi")
                                }
                                Text(isTestingConnection ? "Testing..." : "Test Connection")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(isTestingConnection ? Color.gray : Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                        .disabled(isTestingConnection)

                        if !testResult.isEmpty {
                            Text(testResult)
                                .font(.caption)
                                .foregroundColor(testResult.contains("✅") ? .green : .red)
                                .multilineTextAlignment(.center)
                        }

                        Button(action: testAllServers) {
                            HStack {
                                Image(systemName: "network")
                                Text("Test All Servers (Auto-Fallback)")
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.purple)
                            .cornerRadius(10)
                        }
                    }
                }

                Section(header: Text("Production Settings")) {
                    VStack(spacing: 8) {
                        Text("Current Production Configuration:")
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        Text("• Server: 192.168.84.130:5001 (Local Network)")
                            .font(.caption)
                            .foregroundColor(.green)

                        Text("• External: 65.190.137.27:5001 (Internet)")
                            .font(.caption)
                            .foregroundColor(.blue)

                        Text("• Localhost: 127.0.0.1:5001 (Fallback)")
                            .font(.caption)
                            .foregroundColor(.orange)

                        Text("• API Key: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Text("✅ Redundant servers with auto-fallback")
                            .font(.caption)
                            .foregroundColor(.green)
                            .fontWeight(.semibold)
                    }
                    .padding(.vertical, 4)
                }

                Section {
                    Button(action: saveAndConnect) {
                        HStack {
                            Image(systemName: "checkmark.circle")
                            Text("Save & Connect")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(serverHost.isEmpty || serverPort.isEmpty)
                }
            }
            .navigationTitle("Server Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveAndConnect()
                    }
                    .disabled(serverHost.isEmpty || serverPort.isEmpty)
                }
            }
            .alert("Connection Result", isPresented: $showingAlert) {
                Button("OK") { }
            } message: {
                Text(testResult)
            }
        }
    }

    private func testConnection() {
        isTestingConnection = true
        testResult = ""

        // Update the client temporarily for testing
        dataManager.bigBeautifulAPIClient.updateServerSettings(host: serverHost, port: serverPort)

        Task {
            do {
                let health = try await dataManager.bigBeautifulAPIClient.healthCheck()
                await MainActor.run {
                    testResult = "✅ Connection successful! Server is responding."
                    isTestingConnection = false
                }
            } catch {
                await MainActor.run {
                    testResult = "❌ Connection failed: \(error.localizedDescription)"
                    isTestingConnection = false
                }
            }
        }
    }

    private func saveAndConnect() {
        // Save the configuration
        dataManager.bigBeautifulAPIClient.updateServerSettings(host: serverHost, port: serverPort)

        // Test the connection
        Task {
            await dataManager.connectToBigBeautifulProgram()
            await MainActor.run {
                presentationMode.wrappedValue.dismiss()
            }
        }
    }

    private func testAllServers() {
        Task {
            let results = await dataManager.bigBeautifulAPIClient.testAllServers()

            var resultText = "Server Test Results:\n\n"
            for result in results {
                let status = result.isAvailable ? "✅" : "❌"
                resultText += "\(status) \(result.config.name): \(result.config.host):\(result.config.port)\n"
                if let error = result.error {
                    resultText += "   Error: \(error)\n"
                }
                resultText += "\n"
            }

            await MainActor.run {
                testResult = resultText
            }
        }
    }
}



struct ServerConfigurationView_Previews: PreviewProvider {
    static var previews: some View {
        ServerConfigurationView()
            .environmentObject(DataManager())
    }
}
