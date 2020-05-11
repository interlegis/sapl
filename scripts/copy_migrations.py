import subprocess
import glob


output_custom = {
    'SUCCESS': '\033[92m',
    'WARNING': '\033[93m',
    'ERROR': '\033[91m',
    'END': '\033[0m',
    'BOLD': '\033[1m'
}

print(output_custom['WARNING'] + output_custom['BOLD'] + "Atenção!" + output_custom['END'])
print(
    "Esse script" + output_custom['BOLD'] + " apaga " + output_custom['END'] + \
    "todas as migrations da branch master e" + output_custom['BOLD'] + " copia " + \
    output_custom['END'] + "as migrations da branch 3.1.x para a master."
)
will_continue = input('Deseja continuar (s/n): ')[0].lower()
if will_continue == "s" or will_continue == "y":
    print("Iniciando.")
    print("Verificando alterações na branch atual.")
    
    changes = subprocess.run("git status -s", shell=True, capture_output=True, universal_newlines=True)
    if changes.stderr:
        print(output_custom['ERROR'] + output_custom['BOLD'] + "ERRO: " + output_custom['END'] + changes.stderr)
        exit(-1)
    if changes.stdout:
        print(
            output_custom['WARNING'] + "\nAtenção: " + output_custom['END'] + \
            "Essa branch possui alterações não commitadas:\n"
        )
        subprocess.run("git status -s", shell=True)
        print(
            "\nSelecione uma opção:\n1)" + output_custom['BOLD'] + " Apagar " + output_custom['END'] + \
            "todas as alterações e continuar.\n2) Sair."
        )
        
        selected_option = input('Opção: ')
        if selected_option == '1':
            print(
                output_custom['BOLD'] + output_custom['WARNING'] + "\nAtenção: " + output_custom['END'] + \
                output_custom['BOLD'] + "Essa opção excluirá todos os tipos de alterações." + output_custom["END"] + \
                "\nAs mudanças a serem submetidas (staged), as mudanças não preparadas para submissão " + \
                "(not staged) e os arquivos não monitorados (untracked) serão excluídos."
            )
            confirm_option_1 = input('Deseja continuar (s/n): ')[0].lower()
            if confirm_option_1 == "s" or confirm_option_1 == "y":
                print("Opção 1 selecionada.")
                print("Apagando alterações.")

                subprocess.run("git reset HEAD .", shell=True, capture_output=True)
                subprocess.run("git checkout .", shell=True, capture_output=True)
                subprocess.run("git clean -f -d", shell=True, capture_output=True)

                changes_not_deleted = subprocess.run(
                    "git status -s", shell=True, capture_output=True, universal_newlines=True
                ).stdout
                if changes_not_deleted:
                    print(
                        output_custom['ERROR'] + output_custom['BOLD'] + "ERRO: " + output_custom['END'] + \
                        "Não foi possível desfazer as alterações. Faça manualmente."
                    )
                    exit(-1)
                else:
                    print(output_custom['SUCCESS'] + "Alterações desfeitas com sucesso." + output_custom['END'])

            else:
                print("Opção 2 selecionada.")
                print("Saindo.")
                exit(0)

        else:
            print("Opção 2 selecionada.")
            print("Saindo.")
            exit(0)

    else:
        print(output_custom['SUCCESS'] + "Branch sem alterações não commitadas." + output_custom['END'])

    print("Acessando branch 3.1.x.")
    subprocess.run("git checkout 3.1.x", shell=True, capture_output=True)

    print("Identificando path do repositório.")
    repo_path = subprocess.run(
        "git rev-parse --show-toplevel", shell=True, capture_output=True, universal_newlines=True
    ).stdout
    repo_path = repo_path[:len(repo_path)-1]
    
    print("Listando paths dos diretórios de migrations dos aplicativos.")
    apps_migrations_dir_path_list = list(glob.glob(repo_path + "/sapl/*/migrations/"))

    print("Iniciando cópia de arquivos para diretório temporário.")
    temp_apps_migrations_dir_path = repo_path + "/temp/"
    subprocess.run("mkdir " + temp_apps_migrations_dir_path, shell=True, capture_output=True)

    print("Copiando os diretórios de migrations dos aplicativos...")
    for app_dir in apps_migrations_dir_path_list:
        names = app_dir.split('/')
        app_name = names[len(names)-3]
        source = repo_path + "/sapl/" + app_name + "/migrations/ "
        
        temp_app_migrations_dir_path = temp_apps_migrations_dir_path + app_name + "/"
        subprocess.run("mkdir " + temp_app_migrations_dir_path, shell=True, capture_output=True)
        
        print(app_name + " - Copiando...")
        subprocess.run("cp -r " + source + temp_app_migrations_dir_path, shell=True, capture_output=True)

        print(app_name + " - Verificando Cópia...")
        copy_fail = subprocess.run(
            "diff -q -r " + source + temp_app_migrations_dir_path + "/migrations/",
            shell=True, capture_output=True, universal_newlines=True
        )
        if copy_fail.stderr or copy_fail.stdout:
            print(
                output_custom['ERROR'] + output_custom['BOLD'] + "ERRO: " + output_custom['END'] + \
                "Cópia não realizada com sucesso."
            )
            subprocess.run("rm -r " + temp_apps_migrations_dir_path, shell=True)
            exit(-1)

    print(output_custom['SUCCESS'] + "Cópias realizadas com sucesso." + output_custom['END'])

    print("Acessando branch master.")
    subprocess.run("git checkout master", shell=True, capture_output=True)

    print("Iniciando cópia de arquivos para a master.")
    print("Substituindo os diretórios de migrations dos aplicativos na branch master...") 
    for app_dir in apps_migrations_dir_path_list:
        names = app_dir.split('/')
        app_name = names[len(names)-3]
        source = temp_apps_migrations_dir_path + app_name + "/migrations/ "
        
        print(app_name + " - Apagando...")
        destiny = repo_path + "/sapl/" + app_name
        subprocess.run("sudo rm -r " + destiny + "/migrations/", shell=True, capture_output=True)

        print(app_name + " - Copiando...")
        subprocess.run("cp -r " + source + destiny + "/", shell=True, capture_output=True)

        print(app_name + " - Verificando Cópia...")
        copy_fail = subprocess.run(
            "diff -q -r " + source + destiny + "/migrations/", shell=True, capture_output=True, universal_newlines=True
        )
        if copy_fail.stderr or copy_fail.stdout:
            print(
                output_custom['ERROR'] + output_custom['BOLD'] + "ERRO: " + output_custom['END'] + \
                "Cópia não realizada com sucesso."
            )
            subprocess.run("rm -r " + temp_apps_migrations_dir_path, shell=True)
            subprocess.run("git checkout .", shell=True, capture_output=True)
            subprocess.run("git clean -f -d", shell=True, capture_output=True)
            exit(-1)

    print(output_custom['SUCCESS'] + "Substituição realizada com sucesso." + output_custom['END'])
    
    print("Excluindo diretório temporário.")
    subprocess.run("rm -r " + temp_apps_migrations_dir_path, shell=True)

    print(output_custom['SUCCESS'] + output_custom['BOLD'] + "SUCCESS" + output_custom['END'])
    exit(0)

else: 
    print("Saindo.")
    exit(0)
