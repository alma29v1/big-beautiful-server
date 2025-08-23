import SwiftUI

struct EmailCampaignDetailView: View {
    @EnvironmentObject var dataManager: DataManager
    @Environment(\.presentationMode) var presentationMode

    let campaign: EmailCampaign
    @State private var recipients: [EmailRecipient] = []
    @State private var isLoadingRecipients = false
    @State private var isSending = false
    @State private var showingAlert = false
    @State private var alertMessage = ""

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Campaign Header
                    CampaignHeaderView(campaign: campaign)

                    // Performance Metrics
                    PerformanceMetricsView(campaign: campaign)

                    // Action Buttons
                    ActionButtonsView(
                        campaign: campaign,
                        isSending: isSending,
                        onSend: sendCampaign,
                        onRefresh: {
                            Task {
                                await loadRecipients()
                            }
                        }
                    )

                    // Recipients List
                    RecipientsListView(
                        recipients: recipients,
                        isLoading: isLoadingRecipients
                    )
                }
                .padding()
            }
            .navigationTitle("Campaign Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
            .alert("Campaign Update", isPresented: $showingAlert) {
                Button("OK") { }
            } message: {
                Text(alertMessage)
            }
            .task {
                await loadRecipients()
            }
        }
    }

    private func loadRecipients() async {
        // Email functionality not available in current API
        isLoadingRecipients = false
    }

    private func sendCampaign() {
        alertMessage = "Email campaign functionality not available in current Big Beautiful Program API."
        showingAlert = true
    }
}

struct CampaignHeaderView: View {
    let campaign: EmailCampaign

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(campaign.name)
                        .font(.title2)
                        .fontWeight(.bold)

                    Text(campaign.subject)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                StatusBadge(status: campaign.status)
            }

            if let sentDate = campaign.sentDate {
                HStack {
                    Image(systemName: "calendar")
                        .foregroundColor(.secondary)
                    Text("Sent: \(formatDate(sentDate))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }

    private func formatDate(_ dateString: String) -> String {
        if let date = ISO8601DateFormatter().date(from: dateString) {
            let formatter = DateFormatter()
            formatter.dateStyle = .medium
            formatter.timeStyle = .short
            return formatter.string(from: date)
        }
        return dateString
    }
}

struct PerformanceMetricsView: View {
    let campaign: EmailCampaign

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Performance Metrics")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                MetricCard(
                    title: "Recipients",
                    value: "\(campaign.totalRecipients)",
                    subtitle: "Total sent",
                    color: .blue,
                    icon: "person.2.fill"
                )

                MetricCard(
                    title: "Opens",
                    value: "\(campaign.opens)",
                    subtitle: "\(Int(campaign.openRate))% rate",
                    color: .green,
                    icon: "envelope.open.fill"
                )

                MetricCard(
                    title: "Clicks",
                    value: "\(campaign.clicks)",
                    subtitle: "\(Int(campaign.clickRate))% rate",
                    color: .orange,
                    icon: "hand.tap.fill"
                )

                MetricCard(
                    title: "Bounces",
                    value: "\(campaign.bounces)",
                    subtitle: "\(Int(campaign.bounceRate))% rate",
                    color: .red,
                    icon: "exclamationmark.triangle.fill"
                )
            }

            if campaign.unsubscribes > 0 {
                MetricCard(
                    title: "Unsubscribes",
                    value: "\(campaign.unsubscribes)",
                    subtitle: "\(Int(campaign.unsubscribeRate))% rate",
                    color: .gray,
                    icon: "person.badge.minus"
                )
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let subtitle: String
    let color: Color
    let icon: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.title3)

                Spacer()
            }

            Text(value)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .fontWeight(.semibold)

                Text(subtitle)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(12)
    }
}

struct ActionButtonsView: View {
    let campaign: EmailCampaign
    let isSending: Bool
    let onSend: () -> Void
    let onRefresh: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text("Actions")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 12) {
                if campaign.status.lowercased() == "draft" {
                    Button(action: onSend) {
                        HStack {
                            if isSending {
                                ProgressView()
                                    .scaleEffect(0.8)
                            } else {
                                Image(systemName: "paperplane.fill")
                            }
                            Text(isSending ? "Sending..." : "Send Campaign")
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(12)
                    }
                    .disabled(isSending)
                }

                Button(action: onRefresh) {
                    HStack {
                        Image(systemName: "arrow.clockwise")
                        Text("Refresh Data")
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.green)
                    .cornerRadius(12)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct RecipientsListView: View {
    let recipients: [EmailRecipient]
    let isLoading: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recipients (\(recipients.count))")
                    .font(.headline)

                Spacer()

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                }
            }

            if recipients.isEmpty && !isLoading {
                Text("No recipients found")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(recipients.prefix(10)) { recipient in
                        RecipientRow(recipient: recipient)
                    }

                    if recipients.count > 10 {
                        Text("and \(recipients.count - 10) more...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.top, 8)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemGray6).opacity(0.3))
        .cornerRadius(12)
    }
}

struct RecipientRow: View {
    let recipient: EmailRecipient

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                if let name = recipient.name, !name.isEmpty {
                    Text(name)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }

                Text(recipient.email)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            HStack(spacing: 8) {
                if recipient.openedAt != nil {
                    Image(systemName: "envelope.open.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                }

                if recipient.clickedAt != nil {
                    Image(systemName: "hand.tap.fill")
                        .foregroundColor(.blue)
                        .font(.caption)
                }

                if recipient.bounced {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                }

                if recipient.unsubscribed {
                    Image(systemName: "person.badge.minus")
                        .foregroundColor(.gray)
                        .font(.caption)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
