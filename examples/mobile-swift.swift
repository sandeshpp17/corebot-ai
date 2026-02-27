import Foundation

func chatCorebot(
    apiUrl: String,
    apiKey: String,
    message: String,
    mode: String = "auto",
    history: [[String: Any]] = [],
    appContext: [String: Any] = [:]
) async throws -> Data {
    let url = URL(string: "\(apiUrl)/chat/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    let payload: [String: Any] = [
        "message": message,
        "history": history,
        "mode": mode,
        "app_context": appContext
    ]
    request.httpBody = try JSONSerialization.data(withJSONObject: payload)
    let (data, _) = try await URLSession.shared.data(for: request)
    return data
}
