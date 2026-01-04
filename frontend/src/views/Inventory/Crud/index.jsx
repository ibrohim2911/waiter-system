import Users from './components/Users'
import Items from './components/Items'
import Tables from './components/Tables'
import MenuItems from './components/MenuItems'

const Crud = () => {
    return (
        <div className="w-full min-h-screen bg-zinc-900 text-white p-6 mb-10">
            <div className="max-w-7xl mx-auto">
                <Users />
                <Items />
                <Tables />
                <MenuItems />
            </div>
        </div>
    )
}

export default Crud