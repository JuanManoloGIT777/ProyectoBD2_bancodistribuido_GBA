document.addEventListener("DOMContentLoaded", function () {
    configurarMenuPanel();
    configurarBotonesCarga();
    configurarScrollPublico();
    activarSeccionDesdeURL();
    cargarBarrasReporte();
    configurarBuscadoresTablas();
    cargarGraficasAdmin();
    ocultarAlertasAutomaticamente();
});


function configurarMenuPanel() {
    const botones = document.querySelectorAll(".menu-link");
    const contenido = document.querySelector(".content");

    botones.forEach(boton => {
        boton.addEventListener("click", function () {
            const seccion = this.dataset.section;

            if (!seccion) return;

            if (this.classList.contains("active")) return;

            mostrarCargaModulo(contenido);

            setTimeout(function () {
                activarSeccion(seccion);
                ocultarCargaModulo(contenido);
                cargarBarrasReporte();
            }, 350);
        });
    });
}


function activarSeccionDesdeURL() {
    const parametros = new URLSearchParams(window.location.search);
    const seccion = parametros.get("seccion");

    if (!seccion) return;

    const existeSeccion = document.getElementById(seccion);

    if (!existeSeccion) return;

    const contenido = document.querySelector(".content");

    mostrarCargaModulo(contenido);

    setTimeout(function () {
        activarSeccion(seccion);
        ocultarCargaModulo(contenido);
        cargarBarrasReporte();

        const alerta = document.querySelector(".alert");

        if (alerta) {
            alerta.classList.add("alerta-animada");

            setTimeout(function () {
                alerta.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }, 250);
        }
    }, 400);
}


function activarSeccion(seccion) {
    const botones = document.querySelectorAll(".menu-link");

    botones.forEach(boton => {
        boton.classList.remove("active");

        if (boton.dataset.section === seccion) {
            boton.classList.add("active");
        }
    });

    document.querySelectorAll(".app-section").forEach(sec => {
        sec.classList.remove("active-section");
    });

    const seccionActiva = document.getElementById(seccion);

    if (seccionActiva) {
        seccionActiva.classList.add("active-section");
    }

    actualizarTitulo(seccion);
}


function mostrarCargaModulo(contenido) {
    if (contenido) {
        contenido.classList.add("content-loading");
    }
}


function ocultarCargaModulo(contenido) {
    if (contenido) {
        contenido.classList.remove("content-loading");
    }
}


function actualizarTitulo(seccion) {
    const titulo = document.getElementById("tituloSeccion");
    const subtitulo = document.getElementById("subtituloSeccion");

    if (!titulo || !subtitulo) return;

    const rutaActual = window.location.pathname;

    const textosAdmin = {
        panel: [
            "Panel Administrativo",
            "Supervisión general, reportes, clientes, cuentas y control interno del sistema bancario."
        ],
        usuarios: [
            "Usuarios",
            "Gestión de usuarios internos y roles autorizados."
        ],
        clientes: [
            "Clientes",
            "Consulta administrativa de clientes registrados por el área operativa."
        ],
        cuentas: [
            "Cuentas",
            "Consulta administrativa de cuentas bancarias asociadas a clientes registrados."
        ],
        reportes: [
            "Reportes",
            "Consulta administrativa de transacciones y actividad financiera."
        ],
        auditoria: [
            "Auditoría",
            "Eventos registrados dentro del sistema bancario."
        ]
    };

    const textosCajero = {
        panel: [
            "Panel Cajero",
            "Registro de clientes, cuentas, depósitos, retiros, transferencias, pagos y anulaciones."
        ],
        clientes: [
            "Clientes",
            "Registro y consulta de clientes bancarios."
        ],
        cuentas: [
            "Cuentas",
            "Apertura y consulta de cuentas bancarias."
        ],
        transacciones: [
            "Transacciones",
            "Depósitos, retiros, transferencias y anulación de operaciones."
        ],
        pagos: [
            "Pagos",
            "Pagos de servicios realizados desde cuentas."
        ]
    };

    const textosAuditor = {
        panel: [
            "Panel Auditor",
            "Consulta de eventos, transacciones, pagos y actividad registrada."
        ],
        auditoria: [
            "Auditoría",
            "Eventos registrados dentro del sistema."
        ],
        transacciones: [
            "Transacciones",
            "Consulta de movimientos bancarios registrados."
        ],
        pagos: [
            "Pagos",
            "Consulta de pagos de servicios registrados."
        ]
    };

    let textos = textosAdmin;

    if (rutaActual.includes("panel_cajero")) {
        textos = textosCajero;
    }

    if (rutaActual.includes("panel_auditor")) {
        textos = textosAuditor;
    }

    titulo.textContent = textos[seccion]?.[0] || "GBA CREDOMATIC";
    subtitulo.textContent = textos[seccion]?.[1] || "Sistema bancario.";
}


function configurarBotonesCarga() {
    const formularios = document.querySelectorAll("form");

    formularios.forEach(formulario => {
        formulario.addEventListener("submit", function () {
            const boton = formulario.querySelector("button[type='submit']");

            if (!boton) return;

            boton.dataset.textoOriginal = boton.textContent.trim();
            boton.textContent = "Procesando...";
            boton.classList.add("btn-loading");
            boton.disabled = true;
        });
    });
}


function configurarScrollPublico() {
    const botones = document.querySelectorAll("[data-scroll-target]");

    botones.forEach(boton => {
        boton.addEventListener("click", function () {
            const destino = this.dataset.scrollTarget;
            const seccion = document.querySelector(destino);

            if (seccion) {
                seccion.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });

    const enlaces = document.querySelectorAll(".public-link");

    enlaces.forEach(enlace => {
        enlace.addEventListener("click", function (evento) {
            const ruta = this.getAttribute("href");

            if (!ruta || !ruta.startsWith("#")) return;

            evento.preventDefault();

            enlaces.forEach(e => e.classList.remove("active"));
            this.classList.add("active");

            const seccion = document.querySelector(ruta);

            if (seccion) {
                seccion.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });
}


function cargarBarrasReporte() {
    const barras = document.querySelectorAll(".chart-bar-fill");

    barras.forEach(barra => {
        const porcentaje = Number(barra.dataset.porcentaje || 0);

        if (porcentaje < 0) {
            barra.style.width = "0%";
            return;
        }

        if (porcentaje > 100) {
            barra.style.width = "100%";
            return;
        }

        barra.style.width = porcentaje + "%";
    });
}


function configurarBuscadoresTablas() {
    const buscadores = document.querySelectorAll(".buscador-tabla");

    buscadores.forEach(input => {
        input.addEventListener("input", function () {
            const texto = this.value.toLowerCase().trim();
            const idTabla = this.dataset.tabla;
            const tabla = document.getElementById(idTabla);

            if (!tabla) return;

            const filas = tabla.querySelectorAll("tbody tr");

            filas.forEach(fila => {
                const contenidoFila = fila.textContent.toLowerCase();

                if (contenidoFila.includes(texto)) {
                    fila.style.display = "";
                } else {
                    fila.style.display = "none";
                }
            });
        });
    });
}


function cargarGraficasAdmin() {
    if (typeof Chart === "undefined") return;

    const datosGraficas = document.getElementById("datosGraficasAdmin");

    if (!datosGraficas) return;

    let pastelLabels = [];
    let pastelValores = [];
    let lineaLabels = [];
    let lineaValores = [];

    try {
        pastelLabels = JSON.parse(datosGraficas.dataset.pastelLabels || "[]");
        pastelValores = JSON.parse(datosGraficas.dataset.pastelValores || "[]");
        lineaLabels = JSON.parse(datosGraficas.dataset.lineaLabels || "[]");
        lineaValores = JSON.parse(datosGraficas.dataset.lineaValores || "[]");
    } catch (error) {
        console.error("Error al leer los datos de las gráficas:", error);
        return;
    }

    const graficaPastel = document.getElementById("graficaPastelAdmin");
    const graficaLinea = document.getElementById("graficaLineaAdmin");

    if (graficaPastel) {
        new Chart(graficaPastel, {
            type: "doughnut",
            data: {
                labels: pastelLabels,
                datasets: [{
                    data: pastelValores,
                    borderWidth: 2,
                    backgroundColor: [
                        "rgba(37, 99, 235, 0.75)",
                        "rgba(22, 163, 74, 0.75)",
                        "rgba(245, 158, 11, 0.75)",
                        "rgba(239, 68, 68, 0.75)",
                        "rgba(14, 165, 233, 0.75)"
                    ],
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "62%",
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        });
    }

    if (graficaLinea) {
        new Chart(graficaLinea, {
            type: "line",
            data: {
                labels: lineaLabels,
                datasets: [{
                    label: "Transacciones",
                    data: lineaValores,
                    borderWidth: 3,
                    tension: 0.35,
                    fill: true,
                    pointRadius: 5,
                    backgroundColor: "rgba(37, 99, 235, 0.12)",
                    borderColor: "rgba(37, 99, 235, 1)",
                    pointBackgroundColor: "rgba(37, 99, 235, 1)"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}


function ocultarAlertasAutomaticamente() {
    const alertas = document.querySelectorAll(".alert");

    alertas.forEach(alerta => {
        setTimeout(function () {
            alerta.style.transition = "opacity 0.45s ease, transform 0.45s ease";
            alerta.style.opacity = "0";
            alerta.style.transform = "translateY(-10px)";

            setTimeout(function () {
                alerta.remove();
            }, 500);
        }, 3500);
    });
}