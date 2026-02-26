import Foundation

func chatCorebot(apiUrl: String, message: String) async throws -> Data {
    let url = URL(string: "\(apiUrl)/chat/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    let payload = ["message": message, "history": []] as [String : Any]
    request.httpBody = try JSONSerialization.data(withJSONObject: payload)
    let (data, _) = try await URLSession.shared.data(for: request)
    return data
}
