//! Optional AI provider boundary. Core commands never instantiate a provider.

use vibeguard_core::VibeGuardError;
pub struct CompletionRequest {
    pub prompt: String,
}
pub struct CompletionResponse {
    pub text: String,
}
pub trait AiProvider: Send + Sync {
    fn name(&self) -> &'static str;
    fn health_check(&self) -> Result<(), VibeGuardError>;
    fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse, VibeGuardError>;
}
pub struct DeterministicProvider;
impl AiProvider for DeterministicProvider {
    fn name(&self) -> &'static str {
        "deterministic"
    }
    fn health_check(&self) -> Result<(), VibeGuardError> {
        Ok(())
    }
    fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse, VibeGuardError> {
        Ok(CompletionResponse {
            text: request.prompt,
        })
    }
}
