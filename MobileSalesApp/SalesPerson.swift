import Foundation

struct SalesPerson: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var email: String
    var phone: String
    var active: Bool
    var createdAt: Date

    init(id: UUID = UUID(), name: String, email: String, phone: String,
         active: Bool = true, createdAt: Date = Date()) {
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.active = active
        self.createdAt = createdAt
    }

    var initials: String {
        let components = name.components(separatedBy: " ")
        if components.count >= 2 {
            return "\(components[0].prefix(1))\(components[1].prefix(1))"
        } else {
            return String(name.prefix(2))
        }
    }

    var formattedPhone: String {
        // Simple phone formatting
        let cleaned = phone.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
        if cleaned.count == 10 {
            let index = cleaned.index(cleaned.startIndex, offsetBy: 3)
            let index2 = cleaned.index(cleaned.startIndex, offsetBy: 6)
            return "(\(cleaned[..<index])) \(cleaned[index..<index2])-\(cleaned[index2...])"
        }
        return phone
    }
}
