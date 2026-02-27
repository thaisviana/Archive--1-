#!/usr/bin/env python3
"""
Script para adicionar certificados do sistema macOS ao certifi.
"""
import os
import subprocess
import certifi

def export_system_certs():
    """Exporta certificados do keychain do macOS para arquivo PEM."""
    try:
        # Exportar certificados do sistema
        result = subprocess.run(
            ['security', 'find-certificate', '-a', '-p', '/System/Library/Keychains/SystemRootCertificates.keychain'],
            capture_output=True,
            text=True,
            check=True
        )
        system_certs = result.stdout
        
        # Exportar certificados do usuário
        result = subprocess.run(
            ['security', 'find-certificate', '-a', '-p', '/Library/Keychains/System.keychain'],
            capture_output=True,
            text=True,
            check=True
        )
        user_certs = result.stdout
        
        return system_certs + "\n" + user_certs
    except subprocess.CalledProcessError as e:
        print(f"Erro ao exportar certificados: {e}")
        return ""

def main():
    certifi_path = certifi.where()
    print(f"Arquivo certifi encontrado em: {certifi_path}")
    
    # Fazer backup
    backup_path = certifi_path + ".backup"
    if not os.path.exists(backup_path):
        with open(certifi_path, 'rb') as f:
            backup_data = f.read()
        with open(backup_path, 'wb') as f:
            f.write(backup_data)
        print(f"Backup criado em: {backup_path}")
    
    # Exportar certificados do sistema
    print("Exportando certificados do sistema macOS...")
    macos_certs = export_system_certs()
    
    if macos_certs:
        # Adicionar ao certifi
        with open(certifi_path, 'a') as f:
            f.write("\n# macOS System Certificates\n")
            f.write(macos_certs)
        print("✅ Certificados do sistema adicionados ao certifi!")
        print(f"Total de linhas adicionadas: {len(macos_certs.splitlines())}")
    else:
        print("⚠️  Nenhum certificado adicional encontrado")
    
    print("\n🔧 Reinicie o servidor para aplicar as mudanças.")

if __name__ == "__main__":
    main()
