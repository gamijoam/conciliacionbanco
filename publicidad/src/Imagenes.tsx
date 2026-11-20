import React from 'react';
import {AbsoluteFill} from 'remotion';
import {AVISO_LEGAL, C, ESLOGAN, WHATSAPP} from './config';
import {Fondo, Marca, TarjetaApp} from './componentes';
import {Chat, Check, Equis} from './iconos';

// Piezas fijas para el feed (1080x1350, formato 4:5) y para historias (1080x1920).

const Titular: React.FC<{children: React.ReactNode; size?: number; color?: string}> = ({children, size = 88, color}) => (
	<div style={{fontSize: size, fontWeight: 800, lineHeight: 1.06, letterSpacing: -size * 0.028, textAlign: 'center', color, textWrap: 'balance'} as React.CSSProperties}>{children}</div>
);

const Contacto: React.FC<{oscuro?: boolean}> = ({oscuro}) => (
	<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
		<div style={{display: 'flex', alignItems: 'center', gap: 20, background: C.verde, color: C.blanco, borderRadius: 999, padding: '22px 40px', boxShadow: '0 14px 34px rgba(18,161,80,.35)'}}>
			<Chat size={50} color={C.blanco} />
			<div style={{fontSize: 38, fontWeight: 700}}>WhatsApp {WHATSAPP}</div>
		</div>
		<div style={{fontSize: 20, color: oscuro ? C.blanco : C.tintaSuave, opacity: oscuro ? 0.6 : 1}}>{AVISO_LEGAL}</div>
	</div>
);

const Columna: React.FC<{children: React.ReactNode; padding?: string}> = ({children, padding = '70px 80px 56px'}) => (
	<AbsoluteFill style={{alignItems: 'center', justifyContent: 'space-between', padding}}>{children}</AbsoluteFill>
);

export const PostAprobado: React.FC = () => (
	<Fondo>
		<Columna>
			<Marca size={46} />
			<Titular>
				¿Te llegó el pago?
				<br />
				<span style={{color: C.marca}}>Compruébalo en segundos.</span>
			</Titular>
			<TarjetaApp referencia="123456" monto="2.000,00" estado="aprobado" ancho={860} />
			<Contacto />
		</Columna>
	</Fondo>
);

export const PostFraude: React.FC = () => (
	<Fondo>
		<Columna>
			<Marca size={46} />
			<div style={{display: 'flex', flexDirection: 'column', gap: 22}}>
				<Titular size={84}>
					¿Te mandan la <span style={{color: C.ambar}}>misma captura</span> dos veces?
				</Titular>
				<div style={{fontSize: 36, textAlign: 'center', color: C.tintaSuave, fontWeight: 500, lineHeight: 1.3}}>
					Te avisamos antes de que entregues la mercancía.
				</div>
			</div>
			<TarjetaApp referencia="123456" monto="2.000,00" estado="ya_usada" ancho={860} />
			<Contacto />
		</Columna>
	</Fondo>
);

const Fila: React.FC<{ok: boolean; texto: string}> = ({ok, texto}) => (
	<div style={{display: 'flex', alignItems: 'center', gap: 16, fontSize: 30, fontWeight: 600, lineHeight: 1.2}}>
		<div style={{width: 46, height: 46, borderRadius: 999, background: ok ? C.verde : C.rojoFondo, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
			{ok ? <Check size={30} color={C.blanco} /> : <Equis size={26} color={C.rojo} />}
		</div>
		{texto}
	</div>
);

export const PostAntesAhora: React.FC = () => (
	<Fondo>
		<Columna>
			<Marca size={46} />
			<Titular size={84}>Verificar un pago móvil</Titular>
			<div style={{display: 'flex', gap: 28, width: '100%'}}>
				<div style={{flex: 1, background: C.blanco, borderRadius: 32, padding: 36, boxShadow: '0 14px 40px rgba(11,31,58,.10)'}}>
					<div style={{fontSize: 30, fontWeight: 800, color: C.rojo, letterSpacing: 2, marginBottom: 28}}>ANTES</div>
					<div style={{display: 'flex', flexDirection: 'column', gap: 26}}>
						<Fila ok={false} texto="Abrir el banco" />
						<Fila ok={false} texto="Usuario, clave y código" />
						<Fila ok={false} texto="Buscar entre cientos de movimientos" />
						<Fila ok={false} texto="Comparar referencia y monto" />
						<Fila ok={false} texto="Repetir con cada pago" />
					</div>
				</div>
				<div style={{flex: 1, background: C.marcaOscura, color: C.blanco, borderRadius: 32, padding: 36, boxShadow: '0 14px 40px rgba(11,46,115,.35)'}}>
					<div style={{fontSize: 30, fontWeight: 800, color: '#7FE0A6', letterSpacing: 2, marginBottom: 28}}>AHORA</div>
					<div style={{display: 'flex', flexDirection: 'column', gap: 26}}>
						<Fila ok texto="Escribes referencia y monto" />
						<Fila ok texto="Te dice si el pago llegó" />
						<Fila ok texto="Te avisa si la captura ya se usó" />
					</div>
					<div style={{marginTop: 56, paddingTop: 30, borderTop: '1px solid rgba(255,255,255,.18)'}}>
						<div style={{fontSize: 62, fontWeight: 800, color: '#7FE0A6', lineHeight: 1}}>Segundos</div>
						<div style={{fontSize: 26, opacity: 0.75, marginTop: 8}}>sin abrir el banco tú mismo</div>
					</div>
				</div>
			</div>
			<Contacto />
		</Columna>
	</Fondo>
);

export const Historia: React.FC = () => (
	<Fondo oscuro>
		<Columna padding="130px 80px 110px">
			<Marca size={56} color={C.blanco} />
			<div style={{display: 'flex', flexDirection: 'column', gap: 30, alignItems: 'center'}}>
				<Titular size={104} color={C.blanco}>
					Deja de entrar
					<br />
					al banco
					<br />
					<span style={{color: '#7FE0A6'}}>por cada pago</span>
				</Titular>
				<div style={{fontSize: 40, textAlign: 'center', opacity: 0.85, lineHeight: 1.3, fontWeight: 500, textWrap: 'balance'} as React.CSSProperties}>{ESLOGAN}</div>
			</div>
			<TarjetaApp referencia="123456" monto="2.000,00" estado="aprobado" ancho={900} />
			<Contacto oscuro />
		</Columna>
	</Fondo>
);
