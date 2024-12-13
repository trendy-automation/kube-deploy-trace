#!/bin/bash

#scp k8s_status_traces.sh username@remote_host:
#ssh username@remote_host 'sudo nohup bash k8s_status_traces.sh &'

# Уникальные имена файлов для логов с временной меткой
TRACE_FILE="k8s_status_traces_$(date +%Y%m%d_%H%M%S).log"

# Функция для логирования с временной меткой
log_trace() {
    echo "$(date +%Y-%m-%d\ %H:%M:%S) - $1" | tee -a "$TRACE_FILE"
}

# Функция для ожидания доступности API сервера
wait_for_k8s_api() {
    log_trace "Ожидание доступности Kubernetes API..."
    while true; do
        # Проверяем доступность API сервера
        if sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods --all-namespaces &> /dev/null; then
            log_trace "Kubernetes API сервер доступен. Продолжаем выполнение скрипта..."
            break
        else
            log_trace "API сервер недоступен, повторная попытка через 5 секунд..."
            sleep 5
        fi
    done
}

# Начало работы скрипта
log_trace "Начало трассировки статусов сущностей Kubernetes..."

# Ожидаем доступности Kubernetes API
wait_for_k8s_api

# Тайм-аут на выполнение скрипта — 15 минут (900 секунд)
timeout_duration="15m"

# Функция для сбора статуса и времени начала/окончания для подов с упрощённой обработкой статусов
track_pods() {
    log_trace "Отслеживание подов..."
    sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -A -w --timestamps | while read line; do
        entity_type="Pod"
        
        # Извлекаем временную метку, namespace, имя пода и статус
        timestamp=$(echo $line | awk '{print $1}')  # Временная метка
        namespace=$(echo $line | awk '{print $2}')  # Namespace
        pod_name=$(echo $line | awk '{print $3}')   # Имя пода
        status=$(echo $line | awk '{print $4}')     # Статус
        
        # Обрезаем статус до двоеточия, если оно есть
        clean_status=$(echo $status | cut -d: -f1)

        # Основные статусы подов
        case "$clean_status" in
            "Pending"|"Init"|"PodInitializing"|"ContainerCreating"|"Running"|"Completed"|"Terminating"|"Error"|"NotReady")
                log_trace "Type: $entity_type, Name: $pod_name, Namespace: $namespace, Status: $clean_status, Start Time: $timestamp"
                ;;
        esac
    done
}

# Функция для сбора статуса и времени начала/окончания для ServiceAccount
track_serviceaccounts() {
    log_trace "Отслеживание ServiceAccount..."
    sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get sa -A -w --timestamps | while read line; do
        entity_type="ServiceAccount"
        
        # Для ServiceAccount: timestamp - 1-й столбец, namespace - 2-й, имя SA - 3-й
        timestamp=$(echo $line | awk '{print $1}')
        namespace=$(echo $line | awk '{print $2}')
        sa_name=$(echo $line | awk '{print $3}')
        
        log_trace "Type: $entity_type, Name: $sa_name, Namespace: $namespace, Start Time: $timestamp"
    done
}

# Функция для сбора статуса и времени начала/окончания для Role
track_roles() {
    log_trace "Отслеживание Role..."
    sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get role -A -w --timestamps | while read line; do
        entity_type="Role"
        
        # Для Role: timestamp - 1-й столбец, namespace - 2-й, имя Role - 3-й
        timestamp=$(echo $line | awk '{print $1}')
        namespace=$(echo $line | awk '{print $2}')
        role_name=$(echo $line | awk '{print $3}')
        
        log_trace "Type: $entity_type, Name: $role_name, Namespace: $namespace, Start Time: $timestamp"
    done
}

# Функция для сбора статуса и времени начала/окончания для RoleBinding
track_rolebindings() {
    log_trace "Отслеживание RoleBinding..."
    sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get rolebinding -A -w --timestamps | while read line; do
        entity_type="RoleBinding"
        
        # Для RoleBinding: timestamp - 1-й столбец, namespace - 2-й, имя RoleBinding - 3-й
        timestamp=$(echo $line | awk '{print $1}')
        namespace=$(echo $line | awk '{print $2}')
        rb_name=$(echo $line | awk '{print $3}')
        
        log_trace "Type: $entity_type, Name: $rb_name, Namespace: $namespace, Start Time: $timestamp"
    done
}

# Функция для сбора статуса и времени начала/окончания для Ingress
track_ingresses() {
    log_trace "Отслеживание Ingress..."
    sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get ingress -A -w --timestamps | while read line; do
        entity_type="Ingress"
        
        # Для Ingress: timestamp - 1-й столбец, namespace - 2-й, имя Ingress - 3-й
        timestamp=$(echo $line | awk '{print $1}')
        namespace=$(echo $line | awk '{print $2}')
        ingress_name=$(echo $line | awk '{print $3}')
        
        log_trace "Type: $entity_type, Name: $ingress_name, Namespace: $namespace, Start Time: $timestamp"
    done
}

# Функция для сбора статуса и времени начала/окончания для CRD (Custom Resource Definitions)
track_crd() {
    log_trace "Отслеживание CRD (Custom Resource Definitions)..."
    
    # Получаем все зарегистрированные CRD
    crds=$(sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get crd -o custom-columns=":metadata.name")

    # Проходим по каждому CRD и отслеживаем изменения
    for crd in $crds; do
        log_trace "Отслеживание CRD: $crd"
        
        # Проверка на зарегистрированность CRD
        if sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get crd "$crd" &> /dev/null; then
            log_trace "CRD $crd зарегистрирован. Начинаем отслеживание..."
            
            # Отслеживание изменений в реальном времени
            sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get "$crd" -A -w --timestamps | while read line; do
                entity_type="CRD"
                
                # Для CRD: timestamp - 1-й столбец, namespace - 2-й, имя CRD - 3-й
                timestamp=$(echo $line | awk '{print $1}')
                namespace=$(echo $line | awk '{print $2}')
                crd_name=$(echo $line | awk '{print $3}')
                
                log_trace "Type: $entity_type, Name: $crd_name, Namespace: $namespace, Status: $status, Start Time: $timestamp"
            done
        else
            log_trace "CRD $crd не зарегистрирован. Пропускаем отслеживание."
        fi
    done
}

# Запуск трассировки для различных типов сущностей с тайм-аутом
timeout $timeout_duration bash -c "
    track_pods
    track_serviceaccounts
    track_roles
    track_rolebindings
    track_ingresses
    track_crd
"

# Завершение работы скрипта
log_trace "Трассировка статусов всех сущностей завершена."
log_trace "Трассировка сохранена в файл: $TRACE_FILE"
