import React from 'react';
import {Composition, Still} from 'remotion';
import {DURACION_VIDEO, VideoPublicidad} from './Video';
import {Historia, PostAntesAhora, PostAprobado, PostFraude} from './Imagenes';

export const Root: React.FC = () => (
	<>
		<Composition id="Video-Reels" component={VideoPublicidad} durationInFrames={DURACION_VIDEO} fps={30} width={1080} height={1920} />
		<Still id="Post-Aprobado" component={PostAprobado} width={1080} height={1350} />
		<Still id="Post-Fraude" component={PostFraude} width={1080} height={1350} />
		<Still id="Post-AntesAhora" component={PostAntesAhora} width={1080} height={1350} />
		<Still id="Historia" component={Historia} width={1080} height={1920} />
	</>
);
