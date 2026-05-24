"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HashA2aApi = void 0;
class HashA2aApi {
    constructor() {
        this.name = 'hasha2aApi';
        this.displayName = 'HashA2A API';
        this.documentationUrl = 'https://github.com/ymiydev-prog/HashA2A';
        this.properties = [
            {
                displayName: 'Server URL',
                name: 'serverUrl',
                type: 'string',
                default: 'http://localhost:8080',
                placeholder: 'http://localhost:8080',
                description: 'URL of the HashA2A server',
            },
            {
                displayName: 'API Key',
                name: 'apiKey',
                type: 'string',
                typeOptions: { password: true },
                default: '',
                description: 'Optional JWT token for authentication',
            },
        ];
    }
}
exports.HashA2aApi = HashA2aApi;
//# sourceMappingURL=HashA2aApi.credentials.js.map