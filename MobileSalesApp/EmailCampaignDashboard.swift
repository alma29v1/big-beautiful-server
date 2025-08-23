import SwiftUI

struct EmailCampaignDashboard: View {
    @EnvironmentObject var dataManager: DataManager
    @State private var isRefreshing = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Sales Analytics Overview
                    SalesAnalyticsOverview()

                    // Quick Actions
                    QuickActionsSection()

                    // Big Beautiful Program Status
                    BigBeautifulStatusSection()
                }
                .padding()
            }
            .navigationTitle("Sales Analytics")
            .refreshable {
                await refreshData()
            }
        }
    }

    private func refreshData() async {
        isRefreshing = true
        await dataManager.refreshBigBeautifulData()
        isRefreshing = false
    }
}

struct EmailStatsOverview: View {
    let stats: EmailStats

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Email Marketing Overview")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                StatCard(
                    title: "Total Campaigns",
                    value: "\(stats.totalCampaigns)",
                    color: .blue
                )

                StatCard(
                    title: "Total Sent",
                    value: formatNumber(stats.totalSent),
                    color: .green
                )

                StatCard(
                    title: "Avg Open Rate",
                    value: "\(Int(stats.averageOpenRate))%",
                    color: .orange
                )

                StatCard(
                    title: "Avg Click Rate",
                    value: "\(Int(stats.averageClickRate))%",
                    color: .purple
                )
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }

    private func formatNumber(_ number: Int) -> String {
        if number >= 1000 {
            return String(format: "%.1fK", Double(number) / 1000.0)
        }
        return "\(number)"
    }
}

struct QuickActionsSection: View {
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)

            HStack(spacing: 12) {
                ActionButton(
                    title: "Refresh Data",
                    icon: "arrow.clockwise",
                    color: .blue
                ) {
                    Task {
                        await dataManager.refreshBigBeautifulData()
                    }
                }

                ActionButton(
                    title: "View Analytics",
                    icon: "chart.bar.fill",
                    color: .green
                ) {
                    // Navigate to analytics
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                Text(title)
                    .font(.caption)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(color)
            .cornerRadius(8)
        }
    }
}

struct RecentCampaignsSection: View {
    let campaigns: [EmailCampaign]
    let onCampaignTap: (EmailCampaign) -> Void

    var recentCampaigns: [EmailCampaign] {
        Array(campaigns.prefix(3))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Campaigns")
                    .font(.headline)
                Spacer()
                Text("\(campaigns.count) total")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if recentCampaigns.isEmpty {
                Text("No campaigns found")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(recentCampaigns) { campaign in
                        EmailCampaignRow(campaign: campaign) {
                            onCampaignTap(campaign)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct AllCampaignsSection: View {
    let campaigns: [EmailCampaign]
    let onCampaignTap: (EmailCampaign) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("All Campaigns")
                .font(.headline)

            if campaigns.isEmpty {
                Text("No campaigns found")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(campaigns) { campaign in
                        EmailCampaignRow(campaign: campaign) {
                            onCampaignTap(campaign)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct EmailCampaignRow: View {
    let campaign: EmailCampaign
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(campaign.name)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)

                        Text(campaign.subject)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 4) {
                        StatusBadge(status: campaign.status)

                        if let sentDate = campaign.sentDate {
                            Text(formatDate(sentDate))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }

                HStack(spacing: 16) {
                    MetricView(title: "Recipients", value: "\(campaign.totalRecipients)")
                    MetricView(title: "Open Rate", value: "\(Int(campaign.openRate))%")
                    MetricView(title: "Click Rate", value: "\(Int(campaign.clickRate))%")

                    Spacer()
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(8)
        }
        .buttonStyle(PlainButtonStyle())
    }

    private func formatDate(_ dateString: String) -> String {
        // Simple date formatting - you might want to improve this
        if let date = ISO8601DateFormatter().date(from: dateString) {
            let formatter = DateFormatter()
            formatter.dateStyle = .short
            return formatter.string(from: date)
        }
        return dateString
    }
}

struct StatusBadge: View {
    let status: String

    var body: some View {
        Text(status.capitalized)
            .font(.caption2)
            .fontWeight(.semibold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(statusColor.opacity(0.2))
            .foregroundColor(statusColor)
            .cornerRadius(8)
    }

    private var statusColor: Color {
        switch status.lowercased() {
        case "sent":
            return .green
        case "draft":
            return .orange
        case "scheduled":
            return .blue
        default:
            return .gray
        }
    }
}

struct MetricView: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
            Text(value)
                .font(.caption)
                .fontWeight(.semibold)
        }
    }
}

struct EmailStatCard: View {
    let title: String
    let value: String
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

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(12)
    }
}

struct SalesAnalyticsOverview: View {
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Sales Analytics Overview")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                StatCard(
                    title: "Total Houses",
                    value: "\(dataManager.totalHouses)",
                    color: .blue
                )

                StatCard(
                    title: "New Houses",
                    value: "\(dataManager.newHouses)",
                    color: .green
                )

                StatCard(
                    title: "Active Incidents",
                    value: "\(dataManager.activeIncidentsCount)",
                    color: .orange
                )

                StatCard(
                    title: "Total Routes",
                    value: "\(dataManager.totalRoutes)",
                    color: .purple
                )
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct BigBeautifulStatusSection: View {
    @EnvironmentObject var dataManager: DataManager

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Big Beautiful Program Status")
                .font(.headline)

            HStack {
                Image(systemName: dataManager.isBigBeautifulConnected ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(dataManager.isBigBeautifulConnected ? .green : .red)
                    .font(.title2)

                VStack(alignment: .leading, spacing: 4) {
                    Text(dataManager.isBigBeautifulConnected ? "Connected" : "Disconnected")
                        .font(.subheadline)
                        .fontWeight(.semibold)

                    if let lastSync = dataManager.lastSyncTimestamp {
                        Text("Last sync: \(lastSync, style: .relative) ago")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        Text("Never synced")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}
