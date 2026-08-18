interface Props {
    title: string;
}

function Header(props: Props) {
    return <h1>{props.title}</h1>;
}
