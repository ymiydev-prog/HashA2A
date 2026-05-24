import { ICredentialType, INodeProperties } from 'n8n-workflow';

export class HashA2aApi implements ICredentialType {
  name = 'hasha2aApi';
  displayName = 'HashA2A API';
  documentationUrl = 'https://github.com/ymiydev-prog/HashA2A';

  properties: INodeProperties[] = [
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
